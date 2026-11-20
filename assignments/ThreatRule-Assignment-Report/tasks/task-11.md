# Task 11 Recommendation

Use the Flex design for baseline rule intake. The 100,000-rule file produced 1.8 million tokens in 69.781 ms at the median, about 1.43 million rules per second on this machine. Time rose roughly with input size over the measured range. This supports batch processing at the requested scale; different rule lengths, identifier distributions and cold I/O may change the result.

For bounded token lengths and typical symbol distributions, the scan is expected to take time proportional to input bytes. The scanner does not retain the input file, but memory grows with unique names and the longest buffered token. Timings do not establish peak memory, worst-case behavior or latency on a slow feed. Parser checks for grammar and field compatibility remain necessary.
