---
Title: The XMOS XMP-64
Date: 2014-12-04
Category: Notes
Tags: computing, electronics
Status: published
---

The XMP-64 is an experimental single-board distributed-memory parallel computer
with 512 hardware threads  and is programmable with a C-like language.  It was
developed by [XMOS](https://www.xmos.com>) in 2009 to demonstrate the
scalablility of the [XS1 architecture](https://en.wikipedia.org/wiki/XCore_XS1).
Since then it has been [discontinued](https://www.xmos.com/published/xmp-64-end-life)
but remains a fascinating device from the point of view of providing a huge amount of
parallelism that is programmable in a simple way. As such, I thought I would
record some details and images of it here.

The XMP-64 board contains a four-by-four grid of [XS1-G4
chips](https://en.wikipedia.org/wiki/XCore_XS1-G), each with four processor
cores, and with core providing eight hardware threads. The G4 chips themselves
are connected in an order-four hypercube topology, with every G4 connected
directly to four others. The G4 has 16 links, so four links are used to connect
each direction.  The data rate of each link is 400 Mbits/second, or 1.6
Gbits/second in each edge of the hypercube. The bisection bandwidth of the
entire network is four times this again, at 6.4 Gbits/second. Each processor
core has 64 KB of SRAM memory and runs at 400 MHz. The whole XMP-64 array
therefore provides 512 threads, 4 MB of memory and a peak performance of 25.6
GOPS. (There are more details in the performance experiment document linked
below)

Since the G4 is an embedded processor, these performance numbers are not
competitive with contemporary CPU or GPU devices; it does however burn only a
few tens of watts of power, provides deterministic (completely predictable)
execution of 512 threads and provides a very simple programming interface.

<div class="text-center">
<a href="{{'XMP-64/xmp64-1.JPG'|asset}}" data-lightbox="xmp64"><img class="thumbnail rounded" src="{{'XMP-64/xmp64-1.JPG'|thumbnail('320x320')}}" alt="XMP-64 top"></a>
<a href="{{'XMP-64/xmp64-2.JPG'|asset}}" data-lightbox="xmp64"><img class="thumbnail rounded" src="{{'XMP-64/xmp64-2.JPG'|thumbnail('320x320')}}" alt="XMP-64 bottom"></a>
<a href="{{'XMP-64/xmp64-3.JPG'|asset}}" data-lightbox="xmp64"><img class="thumbnail rounded" src="{{'XMP-64/xmp64-3.JPG'|thumbnail('320x320')}}" alt="XMP-64 top/down"></a>
<a href="{{'XMP-64/xmp64-4.JPG'|asset}}" data-lightbox="xmp64"><img class="thumbnail rounded" src="{{'XMP-64/xmp64-4.JPG'|thumbnail('320x320')}}" alt="XMP-64 left side"></a>
<a href="{{'XMP-64/xmp64-5.JPG'|asset}}" data-lightbox="xmp64"><img class="thumbnail rounded" src="{{'XMP-64/xmp64-5.JPG'|thumbnail('320x320')}}" alt="XMP-64 right side"></a>
<a href="{{'XMP-64/xmp64-6.JPG'|asset}}" data-lightbox="xmp64"><img class="thumbnail rounded" src="{{'XMP-64/xmp64-6.JPG'|thumbnail('320x320')}}" alt="XMP-64 in case"></a>
</div>

As you can see in the pictures, there are two Ethernet interfaces at the top of
the board, which could be used to daisy chain multiple XMP-64 boards together.
Additionally there are 64-pin headers on either side that expose
general-purpose I/O pins connected directly to processors in the array.

Below is an example program for the XMP-64 written in
[XC](https://en.wikipedia.org/wiki/XC_(programming_language)), a programming
language based on
[occam](https://en.wikipedia.org/wiki/Occam_(programming_language)) designed to
target the features of the XS1 architecture. The program uses a ring topology
of communication channels to connect one thread on each chip. As a token is
passed around, the LED connected to each G4 is switched on for a short period.

```javascript
#include <platform.h>
#include <xs1.h>

#define NUM_CHIPS (16)
#define STEP      (4)

out port leds[] = {
  on stdcore[0] : XS1_PORT_1E,
  on stdcore[4] : XS1_PORT_1E,
  on stdcore[8] : XS1_PORT_1E,
  on stdcore[12]: XS1_PORT_1E,
  on stdcore[16]: XS1_PORT_1E,
  on stdcore[20]: XS1_PORT_1E,
  on stdcore[24]: XS1_PORT_1E,
  on stdcore[28]: XS1_PORT_1E,
  on stdcore[32]: XS1_PORT_1E,
  on stdcore[36]: XS1_PORT_1E,
  on stdcore[40]: XS1_PORT_1E,
  on stdcore[44]: XS1_PORT_1E,
  on stdcore[48]: XS1_PORT_1E,
  on stdcore[52]: XS1_PORT_1E,
  on stdcore[56]: XS1_PORT_1E,
  on stdcore[60]: XS1_PORT_1E
};

void flash_led(int id, chanend prev, chanend next, out port led) {
  timer t;
  if (id == 0) {
    next <: 1;
  }
  while (1) {
    prev :> void;
    led <: 1;
    delay_milliseconds(100);
    led <: 0;
    next <: 1;
  }
}

int main() {
  chan c[NUM_CHIPS];
  par {
    par (int i = 0; i < NUM_CHIPS; i += STEP) {
      on stdcore[i] : flash_led(i, c[i], c[(i + 1) % NUM_CHIPS], leds[i / STEP]);
    }
  }
  return 0;
}
```

As an intern at XMOS in 2009, I did some work to investigate the performance of
the XMP-64. This is written up in the document linked below. It looks at the
performance of barrier synchronisations and exchanges of various permutations
of source-destination pairs. Sadly though, to my knowledge, the XMP-64 didn't
see much further use or experimental application development. However, a
similar board was developed by the [Swallow
project](https://www.cs.bris.ac.uk/home/simon/many-core/Swallow/Swallow.html),
which used XS1 chips (12 cores per board) and allowed direct expansion of the
network with multiple boards up to 480 cores. See the [research
paper](http://arxiv.org/pdf/1504.06357.pdf) (ArXiv) for more details.

More information and links
--------------------------

* [XMP-64 performance experiments document](/files/xmp64experiments.pdf) (PDF), 2010,

* [XMP-64 performance experiments source code](https://github.com/jameshanlon/xmp64-experiments) (GitHub).

* [The XMOS XK-XMP-64 development board](http://ieeexplore.ieee.org/document/5948572), a writeup based on the
  above for the Networks on Chip 2011 symposium, (IEEE Xplore).

* [Example programs and PCB design files](https://github.com/xcore/proj_xmp64) (GitHub).

* [XCore wiki page](https://www.xcore.com/wiki/index.php/XK-XMP-64_Development_Board).

* [XK-XMP-64 Development Board](https://www.xmos.com/xmp64) (XMOS website).
