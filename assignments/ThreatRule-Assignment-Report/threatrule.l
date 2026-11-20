%option noyywrap nodefault noinput nounput yylineno never-interactive
%s FEED
%{
#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* Text attributes point to yytext until the next yylex call. */
enum Token { RULE=256, IF, AND, OR, THEN, ALERT, BLOCK, ID, INTEGER,
             PORT, IPV4, STRING, RELOP, SEMI, HASH, CVE, URL, END_TOKEN };
static const char *names[] = {"RULE","IF","AND","OR","THEN","ALERT","BLOCK",
    "ID","INTEGER","PORT","IPV4","STRING","RELOP","SEMI","HASH","CVE","URL"};
static union { uint64_t number; uint32_t ip; size_t symbol; const char *text; } yylval;
enum Context { OTHER, PORT_FIELD, PORT_VALUE };
static enum Context context;
static size_t errors;
static int quiet_errors;
static size_t intern(const char *s);
static int ipv4(const char *s);
static void issue(const char *reason);
static int number(void);
#define PLAIN(t) do { context = OTHER; return (t); } while (0)
#define TEXT(t) do { yylval.text = yytext; PLAIN(t); } while (0)
%}

D       [0-9]
H       [0-9A-Fa-f]
IDENT   [A-Za-z_][A-Za-z_0-9]*
IPLIKE  {D}+([.]{D}*)+
BODY    ([^"\\\r\n]|\\["\\nrt])
TAIL    ([^"\\\r\n]|\\[^\r\n])
HASH    ({H}{32}|{H}{40}|{H}{64})
CVE     CVE-{D}{4}-{D}{4,}
LABEL   [A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?
HOST    {LABEL}([.]{LABEL})+
WEB     https?:\/\/{HOST}(:{D}+)?([/?#][A-Za-z0-9._~:/?\[\]@!$&'()*+,=%#-]*)?

%%
 /* Reserve exact uppercase keywords; a longer identifier still wins. */
"RULE"   { PLAIN(RULE); }
"IF"     { PLAIN(IF); }
"AND"    { PLAIN(AND); }
"OR"     { PLAIN(OR); }
"THEN"   { PLAIN(THEN); }
"ALERT"  { PLAIN(ALERT); }
"BLOCK"  { PLAIN(BLOCK); }

 /* Valid feed forms precede broad candidates for single-error recovery. */
<FEED>{HASH}                        {
    if (context == PORT_VALUE && strspn(yytext,"0123456789") == (size_t)yyleng) {
        int t = number(); if (t) return t;
    } else { TEXT(HASH); }
}
<FEED>{CVE}                         { TEXT(CVE); }
<FEED>{WEB}                         { TEXT(URL); }
<FEED>CVE-[^ \t\r\n;<>!="]*         { issue("invalid CVE"); }
<FEED>https?:\/\/[^ \t\r\n;<>"]*      { issue("invalid URL"); }

{IPLIKE}            {
    if (context == PORT_VALUE) issue("expected a decimal port");
    else if (ipv4(yytext)) PLAIN(IPV4);
    else issue("invalid IPv4 address");
}
{D}+                { int t = number(); if (t) return t; }
{IDENT}             {
    yylval.symbol = intern(yytext);
    context = !strcmp(yytext,"port") ? PORT_FIELD : OTHER;
    return ID;
}
\"{BODY}*\"       { TEXT(STRING); }
\"{TAIL}*\"       { issue("invalid string escape"); }
\"{TAIL}*(\\)?    { issue("unterminated string"); }
"=="|"!="|"<="|">="|"<"|">" {
    yylval.text = yytext;
    context = context == PORT_FIELD ? PORT_VALUE : OTHER;
    return RELOP;
}
";"                 { PLAIN(SEMI); }
#[^\r\n]*          { /* comment ends before newline */ }
[ \t\f\v]+         { /* preserve context across horizontal whitespace */ }
\r?\n              { context = OTHER; }
.                   { issue("unexpected character"); }
%%

/* Open addressing keeps expected lookup constant as unique names grow. */
struct Entry { char *name; size_t id; };
static struct Entry *symbols;
static size_t used, capacity;
static void fail(const char *msg) { fprintf(stderr,"%s\n",msg); exit(2); }
static size_t slot(const char *s, size_t cap) {
    uint64_t h = UINT64_C(14695981039346656037);
    for (; *s; ++s) h = (h ^ (unsigned char)*s) * UINT64_C(1099511628211);
    size_t i = (size_t)h & (cap-1);
    return i;
}
static size_t locate(const char *s, struct Entry *table, size_t cap) {
    size_t i = slot(s,cap);
    while (table[i].name && strcmp(table[i].name,s)) i = (i+1)&(cap-1);
    return i;
}
static size_t intern(const char *s) {
    if (!capacity || (used+1)*10 > capacity*7) {
        size_t cap = capacity ? capacity*2 : 256;
        struct Entry *next = calloc(cap,sizeof *next);
        if (!next) fail("out of memory");
        for (size_t i=0;i<capacity;++i)
            if (symbols[i].name) next[locate(symbols[i].name,next,cap)] = symbols[i];
        free(symbols);
        symbols = next; capacity = cap;
    }
    size_t i = locate(s,symbols,capacity);
    if (!symbols[i].name) {
        size_t n = strlen(s)+1;
        symbols[i].name = malloc(n);
        if (!symbols[i].name) fail("out of memory");
        memcpy(symbols[i].name,s,n);
        symbols[i].id = ++used;
    }
    return symbols[i].id;
}

static void issue(const char *reason) {
    ++errors;
    context = OTHER;
    if (!quiet_errors)
        fprintf(stderr,"line %d: %s near `%.*s%s`\n",yylineno,reason,
                (int)(yyleng > 80 ? 80 : yyleng),yytext,yyleng > 80 ? "..." : "");
}

static int number(void) {
    int port = context == PORT_VALUE;
    errno = 0;
    uintmax_t value = strtoumax(yytext,NULL,10);
    if (errno == ERANGE || value > UINT64_MAX || (port && value > 65535)) {
        issue(port ? "port outside 0..65535" : "integer outside uint64 range");
        return 0;
    }
    context = OTHER;
    yylval.number = (uint64_t)value;
    return port ? PORT : INTEGER;
}

static int ipv4(const char *s) {
    uint32_t packed = 0;
    for (int i=0;i<4;++i) {
        unsigned v=0, digits=0;
        while (*s >= '0' && *s <= '9') {
            if (++digits > 3) return 0;
            v = 10*v + (unsigned)(*s++ - '0');
        }
        if (!digits || v>255) return 0;
        packed = (packed<<8)|v;
        if (i<3 && *s++ != '.') return 0;
    }
    if (*s) return 0;
    yylval.ip = packed;
    return 1;
}

int main(int argc,char **argv) {
    int feed=0, dump=0;
    const char *path=NULL;
    for (int i=1;i<argc;++i) {
        if (!strcmp(argv[i],"--feed")) feed=1;
        else if (!strcmp(argv[i],"--dump")) dump=1;
        else if (!strcmp(argv[i],"--quiet-errors")) quiet_errors=1;
        else if (argv[i][0]=='-' || path) fail("usage: scanner [--feed] [--dump] [--quiet-errors] [file]");
        else path=argv[i];
    }
    if (path && !(yyin=fopen(path,"rb"))) { perror(path); return 2; }
    if (!path) yyin=stdin;
    if (feed) BEGIN(FEED);
    size_t count[END_TOKEN-RULE]={0}, total=0;
    struct timespec start,end;
    clock_gettime(CLOCK_MONOTONIC,&start);
    int t;
    while ((t=yylex())) {
        ++count[t-RULE]; ++total;
        if (!dump) continue;
        printf("%d\t%s\t%.*s",yylineno,names[t-RULE],(int)yyleng,yytext);
        if (t==ID) printf("\tid=%zu",yylval.symbol);
        if (t==INTEGER || t==PORT) printf("\tvalue=%" PRIu64,yylval.number);
        if (t==IPV4) printf("\tvalue=0x%08" PRIX32,yylval.ip);
        if (t==STRING || t==RELOP || t==HASH || t==CVE || t==URL)
            printf("\ttext=%s",yylval.text);
        puts("");
    }
    clock_gettime(CLOCK_MONOTONIC,&end);
    double ms=(end.tv_sec-start.tv_sec)*1000.0+(end.tv_nsec-start.tv_nsec)/1e6;
    printf("tokens=%zu errors=%zu identifiers=%zu hash=%zu cve=%zu url=%zu ms=%.6f\n",
           total,errors,used,count[HASH-RULE],count[CVE-RULE],count[URL-RULE],ms);
    if (path) fclose(yyin);
    yylex_destroy();
    for (size_t i=0;i<capacity;++i) free(symbols[i].name);
    free(symbols);
    return errors ? 1 : 0;
}
