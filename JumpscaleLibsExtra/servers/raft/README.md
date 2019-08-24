# Raft

This implementation of raft is using pysyncobj

It is a very nice highly effective library, need to fix some issue we are seeing though.

While testing on my mac OSX I could not get it to work stable (I think has been reproduced on linux now as well).
When killing nodes, the catchup did not work well.

we need to test this implementation well, come up with strategies where we have lots of load & kill nodes.
Do up to 50 nodes, see what happens if random nodes get killed.
Ofcourse test very well for 3 too because its easier to spot issues.

see also https://github.com/bakwc/PySyncObj/issues/78
