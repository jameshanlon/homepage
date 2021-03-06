---
Title: Writing synthesizable Verilog
Date: 2018-5-4
Category: notes
Tags: computing, microelectronics, Verilog
Status: published
---

In the last year, I've started from scratch writing Verilog for hardware
design. Coming from a software background where I was mainly using C/C++ and
Python, it has been interesting to experience the contrasting philosophy and
mindset associated with using a language to describe hardware circuits. Much of
this is because Verilog provides little abstraction of hardware structures, and
only through disciplined/idiomatic use, can efficient designs be implemented. A
compounding issue is that complex hardware designs rely on a complex
ecosystem of proprietary tooling.

As I see it, there are three aspects to writing synthesizable Verilog code: the
particular features of the language to use, the style and idioms employed in
using those features, and the tooling support for a design.

### The language

A subset of Verilog is used for specifying synthesizable circuits. Verilog
(which subsumed SystemVerilog as of the 2009 standardisation) is a unified
language, serving distinct purposes of modern hardware design. These are:

- circuit design/specification at different levels of abstraction:
    * behavioural
    * structural/register-transfer level (RTL)
    * gate
    * switch/transistor;
- testbench-based verification;
- specification of formal properties; and
- specification of functional coverage.

The language provides specific features to serve each of these purposes. For
hardware synthesis, each level of abstraction uses a different language subset,
generally with fewer features at lower levels. Behavioural design uses the
procedural features of Verilog (with little regard for the structural
realisation of the circuit). RTL design specifies a circuit in terms of data
flow through registers and logical operations. Gate- and switch-level design
use only primitive operations. Typical modern hardware design uses a mix of
register-transfer- and gate-level design.

It is interesting to note however that the specification of Verilog does not
specify which features are synthesizable; that depends on the tooling used.

### Coding style

Good coding style can help achieve better results in synthesis and simulation,
as well as producing code that contains less errors and is understandable,
reusable, and easily modifiable. Many of the observations in this note relate
to coding style.

### Tooling

There is a variety of standard tooling that is used with Verilog, and indeed
other hardware description languages (HDLs). This includes simulation, formal
analysis/model checking, formal equivalence checking, coverage analysis,
synthesis and physical layout, known collectively as electronic design
automation tools (EDA). Since standard EDA tooling is developed and maintained
as proprietary and closed-source software by companies like Cadence, Synopsis
and Mentor, the tooling options are multiplied.

In contrast with the open-source software ecosystems of programming languages
(for example), closed-source EDA tools do not benefit from the scale and
momentum of open projects, in the way that conventional software languages do,
with a one (or perhaps two) compilers and associated tooling such as debuggers
and program analysers. Such a fragmented ecosystem inevitably has a larger
variability in precisely how features of the Verilog language are implemented
and which features are not supported, particularly since there is no standard
synthesizable subset. Consequently, engineers using Verilog/HDLs with
proprietary EDA tools do so conservatively, sticking to a lowest common
denominator of the language features (within their chosen synthesizable
subset), to ensure compatibility and good results.

## Overview

This note records some interesting Verilog approaches and coding styles that
I've observed that are used to interact well with the supporting tooling and to
produce good synthesis results. I've written it as a note to myself, so it has
the caveats that it assumes a familiarity with Verilog programming and that
it's not a comprehensive guide to Verilog programming practices; some of the
references at the end will serve those purposes better.

My observations here are in the context of work on an implementation of a
pipelined processor, as such different approaches may be taken with other types
of electronic design. I also owe many of these insights to the guidance from my
colleagues.

The remaining sections are as follows:

- [Combinatorial logic](#comb-logic)
- [Sequential logic](#seq-logic)
- [If statements](#if-statements)
- [Case statements](#case-statements)
- [Expressions](#expressions)
- [Code structure](#code-structure)
- [Signal naming](#signal-naming)

<a name="comb-logic"></a>
## Combinatorial logic

**Use `always_comb` instead of `always` for combinatorial logic.** The
`always_comb` procedure allows tools to check that it does not contain any
latched state and that no other processes assign to variables appearing on the
left-hand side. (It's worth checking the language reference manual (LRM) for
details of of the other differences.) The use of an `always_comb` block is also
a much clearer indication of a combinatorial block that the use of `=` as
opposed to `<=`.

**Always provide an initial value.** A latch will be inferred if there exists a
control-flow path in which a value of a signal is not set. Since `always_comb`
specifically precludes the creation of latches, doing so will cause a warning
or error in simulation or synthesis. For example, the following code implies a
latch since there is no assignment to `foo` when the condition is not true.

```
always_comb
  if (condition)
    foo = 1'b1;
```

Instead, always provide an initial value:

```
always_comb
  foo = 1'b0;
  if (condition)
    foo = 1'b1;
```

**Avoid reading and writing a signal in an `always_comb` block.** The
sensitivity list includes variables and expressions
but it excludes variables that occur on the right-hand side of assignments.
According to these restrictions, a variable that is read and written in a block
only causes the block to be reevaluated when the left-hand-side instance
changes. However, this style can cause some tools to warn of a
simulation-synthesis mismatch (presumably because they apply conservative rules
from older versions of the language standard).

In the following code, the block is triggered only when the the right-hand-side
`foo` changes, rather than entering a feedback loop where it shifts
continuously:

```
always_comb
  foo = foo << 1;
```

To avoid reading and writing foo in the same block and possible warnings
from tools, a new signal can be introduced:

```
always_comb
  next_foo = foo << 1;
```

**Where possible extract logic into `assign` statements.** Extract single
assignments to a variable into a separate `assign` statement, where it is
possible to do so. This approach uses the features of Verilog consistently,
rather than using two mechanisms to achieve the same effect. This makes it
clear that an `always_comb` is used to introduce sequentiality. Another
opportunity to move logic into separate `assign` statements is with complex
expressions, such as the Boolean value for a conditional statement. Doing this
makes the control flow structure clearer, potentially provide opportunities for
reuse, and provides a separate signal when inspecting the signals in a waveform
viewer.

**Avoid unnecessary sequentiality.** It is easy to add statements to an
`always_comb` to expand its behaviour, but this should only be done when there
are true sequential dependencies between statements in the block. In general,
parallelism should be exposed where ever possible. In the the following
example, the sequentiality is not necessary since the output `set_foo` depends
independently on the various conditions:

```
always_comb begin
  set_foo = 1'b0;
  if (signal_a &&
      signal_b)
    set_foo = 1'b1;
  if (signal_c ||
      signal_d)
    set_foo = 1'b1;
  if (signal_e)
    set_foo = 1'b1;
end
```

Clearly the sequencing of the conditions is not necessary, so the block could
be transformed to separate the logic for each condition into separate parallel
processes (extracting into `assign` statements as per the rule above) and
explicitly combine them with the implied logical disjunction of the original
block:

```
assign condition_a = signal_a && signal_b;
assign condition_b = signal_c || signal_d;
always_comb begin
  set_foo = 1'b0;
  if (condition_a ||
      condition_b ||
      signal_e)
    set_foo = 1'b1;
end
```

It is [recommended][verilator-internals] by the author of Verilator to split up
``always`` blocks (combinatorial or sequential) so they contain as few
statements as possible. This allows Verilator the most freedom to order the
code to improve execution performance.

**Drive one signal per block.**
With complex control flow statements, it is tempting to use a single
`always_comb` block to drive multiple signals. In some circumstances, there may
be good reasons to do this, such as when many output signals are used in a
similar way, but in the general case, splitting each signal into a separate
block makes it clear what logic involved in driving that signal, and as such,
facilitates further simplification.

An additional reason to avoid driving multiple signals per `always_comb` block
is that [Verilator][verilator] can infer a dependence between two signals,
leading to false circular combinatorial loops. In these cases, it issues an
[`UPOPTFLAT` warning][unoptflat] and cannot optimise the path, leading to
reduced emulation performance. Generally, fixing warnings pertaning to
unoptimisable constructs can improve Verilator's simulation performance by [up
to a factor of two][verilator-internals].

[verilator-internals]: https://www.veripool.org/papers/verilator_philips_internals.pdf
[verilator]: https://www.veripool.org/wiki/verilator
[unoptflat]: https://www.embecosm.com/appnotes/ean6/html/ch07s02s07.html

```
always_comb begin
  foo = foo_q;
  bar = bar_q;
  if (condition_a)
    case (condition_b)
      0: begin
        foo = ...;
        if (condition_c)
          bar = ...;
      end
      1: foo = ...;
      2: bar = ...;
      default:;
    endcase
end
```
The above block could be split into two processes:
```
always_comb begin
  foo = foo_q;
  if (condition_a)
    case (condition_b)
      0: foo = ...;
      1: foo = ...;
      default:;
    endcase
end

always_comb begin
  bar = bar_q;
  if (condition_a)
    case (condition_b)
      0: if (condition_b)
           bar = ...;
      2: bar = ...;
      default:;
    endcase
end
```

<a name="seq-logic"></a>
## Sequential logic

**Use `always_ff` instead of `always` for sequential logic** Similarly to
`always_comb`, use of `always_ff` permits tools to check that the procedure
only contains sequential logic behaviour (no timing controls and only one event
control) that variables on the left-hand side are not written to by any other
process, and makes clear the intent for sequential logic behaviour with
non-blocking assignments, `<=`.

**Avoid adding logic to non-blocking assignments.** This is primarily a matter
of taste, but having non-blocking assignments in `always_ff` blocks only from a
logic signal name, rather than a logical expression, keeps the block simple and
limits combinatorial logic to `always_comb` blocks and `assign` statements
elsewhere in the module. Since synthesizable `always_ff`s are additionally
restricted in that variables assigned to must have a reset condition of a
constant value, maintaining this clarity aids the programmer. Having separate
combinatorial blocks is also useful since it allows the logic signal driving a
flip-flop as well as the registered value to be apparent in a waveform viewer,
particularly when clock gates are used.

A typical pattern when implementing combinatorial logic and registers is to
define the set and clear conditions in an `always_comb` and register the value
in an accompanying `always_ff`, for example:

```
logic bit;
logic bit_q;

always_comb begin
  bit <= bit_q;
  if (set_condition)
    bit = 1'b1;
  if (clear_condition)
    bit = 1'b0;
end

always_ff @(posedge i_clk or posedge i_rst)
  if (i_rst)
    bit_q <= 1'b0;
  else
    bit_q <= bit;
```

<a name="if-statements"></a>
## If statements

**Use `if` qualifiers** for single `if` and chained `if-else`
statements for additional checking and guidance to synthesis:

 - `unique` to ensure exactly one condition is matched and to indicate the
   conditions can be checked in parallel.
 - `unique0` to ensure one or no conditions match and to indicate the
   conditions can be checked in parallel.
 - `priority` to ensure one condition is matched and to indicate the conditions
   should be evaluated in sequence and only the body of the first matching
   condition is evaluated.

Note that:

- The use of an `else` precludes violation reports for non-existing matches in
  `unique` and `priority`.
- The default behaviour of a chained `if-else` block is `priority` but without
  any violation checks.

For example, when the conditions are mutually exclusive, so evaluation order is
not important:
```
unique if (condition_a) statement;
else if (condition_b) statement;
else if (condition_c) statement;
```
A violation warning is given in the above when no condition or multiple conditions are
selected. Changing to `unique0` will only check for multiple conditions being selected:
```
unique0 if (condition_a) statement;
...
```
And adding an `else` will suppress violation warnings all together:
```
unique0 if (condition_a) statement;
...
else statement;
```

<a name="case-statements"></a>
## Case statements

**Use case qualifiers** for additional checking and guidance to synthesis:

 - `unique` to ensure exactly one condition is matched and to indicate the
   conditions can be checked in parallel.
 - `unique0` to ensure that one or no conditions are matched and to indicate
   the conditions can be checked in parallel.
 - `priority` to ensure one condition is matched and to indicate the conditions
   should be evaluated in sequence and only the body of the first matching case
   is evaluated.

Note that:

 - The use of a `default` case precludes violation reports for non-existing matches in `unique` and `priority`.
 - The default behaviour of a `case` statement is that of `priority`, but without violation checks.

**Use `case (...) inside` instead of `casex` or `casez` for matching don't care
bits.** Since set-membership `case (...) inside` matches `?` don't care bits in
the same way `casez` does, it should be used for clarity unless matching `x`s
or `z`s is specifically required. For example:

```
logic [3:0] state_q;
case (state_q) inside
  4'b000?: statement;
  4'b01?0: statement;
  4'b110?: statement;
endcase
```

**Use `case (1'b1)` for one-hot conditions.** For example:

```
logic [2:0] status_q;
unique case (1'b1) inside
  status_q[0]: statement;
  status_q[1]: statement;
  status_q[2]: statement;
endcase
```

As an aside, it is convenient to define a one-hot encoding in a union type with
another struct to provide named access to each member. For example, `status_q`
above could be redefined as:
```
typedef enum logic [2:0] {
  STATUS_START = 3'b001,
  STATUS_END   = 3'b010,
  STATUS_ERROR = 3'b100
} status_enum_t;
typedef union packed {
  status_enum_t u;
  struct packed {
    logic status_start;
    logic status_end;
    logic status_error;
  } ctrl;
} status_t;
status_t status_q;
```

**Minimise the amount of logic inside a case statement.** The rationale for
this is similar to extracting logic from `always_comb` blocks into `assign`
statements where possible: to make the control flow structure clearer to the
designer and tooling, and to provide opportunities for reuse or
further simplification. For example, avoid nesting `case` statements:

```
status_t status_q;
status_t next_status;
logic [3:0] mode_q;
always_comb begin
  next_status = state_q;
  unique case(1'b1)
    status_q.ctrl.stat_start:
      unique0 case (mode) inside
        4'b000?,
        4'b0?00: next_status = STATUS_ERROR;
        default: next_status = STATUS_END;
      endcase
    status_q.ctrl.status_end: ...;
    status_q.ctrl.status_error: ...;
  endcase
end
```

And instead extract a nested `case` into a separate process, providing a
result signal to use in the parent case:
```
status_t status_q;
status_t next_status;
status_t start_next_status;
logic [3:0] mode_q;
always_comb begin
  start_next_status = state_q;
  case (mode_q) inside
    4'b000?,
    4'b0?00: start_next_status = STATUS_ERROR;
    default: start_next_status = STATUS_END;
  endcase
end
always_comb begin
  unique case(1'b1)
    status_q.ctrl.status_start: next_status = start_next_status;
    status_q.ctrl.status_end: ...;
    status_q.ctrl.status_error: ...;
  endcase
end
```

Although this example seems simple, the `case`-based logic driving a state
machine can quickly become complicated.

<a name="expressions"></a>
## Expressions

**Make operator associativity explicit.** This is to avoid any ambiguity over
the ordering of operators. In particular, always bracket the condition of a
ternary/conditional expression (`?:`), especially if you are nesting them,
since they associate left to right, and all other arithmetic and logical
operators associate right to left.

```
... = (a && b) ||
      (c && d)
... = |(a[7:0] & b[7:0])
... = valid && (|a[3:0])
... = (a == b) ? c : d
... = cond_a              ? e1 :
      (cond_b && !cond_c) ? e2 :
                            e3
... = !(a[1:0] inside {2'b00, 2'b01}) &&
      ^(b[31:0])
```

**Make expression bit lengths explicit.** Although the Verilog language
specification provides rules for the extension of operands as inputs to binary
operations and assignments, these are complicated and not always obvious. In
particular, the extension is determined either by the operands or by the
context of the expression. Since there may be inconsistencies between tools,
particularly between simulation and synthesis, explicitly specifying expression
bit widths avoids these issues and makes the intent obvious. For example, pad
the result of a narrower expression for assignment:

```
logic [31:0] result;
logic [7:0] op1, op2;
assign result = {24'b0, {op1 & op2}};
```

Use an explicit type cast to specify the width of an intermediate expression
(note that integer literals are interpreted as 32-bit integers):

```
always_ff @(posedge i_clk or posedge i_rst)
  value_q <= i_rst ? value_t'(42) : value;
```

Special care should be taken with sub expressions, since their result length is
determined automatically by the width of the largest operand. For example,
without an explicit type cast to a 17-bit result around `a + b`, the carry out
bit would be lost:
```
logic [15:0] result, a b;
typedef logic [16:0] sum_t;
assign result = sum_t'(a + b) >> 1;
```

Capture carry out bits (even if they are unused) so the left-hand-side
assignment width matches the full width of the right hand side. Using a prefix
like `unused_` makes the process of signing off any related warnings with the
downstream synthesis and physical build simpler:
```
assign {unused_co, result} = a + b;
```

Exceptions to this rule can be made for the common constants 0, 1 and -1 to be
specified as `integer` literals, for example:
```
assign result = 0;
assign sum = value - 1;
```

**Use `signed` types for signed arithmetic,** and avoid implementing signed
arithmetic with manual sign extensions. Verilog uses the signedness of an
expression to determine how to extend its width (as well as inferring
signedness of parent expressions). Since the rules for sign determination is
similar to expression size but not the same, making it explicit avoids errors.
It also facilitates the use of optimised arithmetic implementations in
synthesis, particularly with multipliers. The following example (adapted from
[this presentation][arithmetic-gotcha])
shows how these rules can be confusing:

```
logic signed [3:0] a, b;
logic signed [4:0] sum;
logic ci;
sum = a + b + ci; // Unsigned addition due to unsigned ci.
sum = a + b + signed'(ci); // Signed addition, but ci == 1'b1 will be
                           // sign extended to 4'b1111 or -1.
sum = a + b + signed'({1'b0, ci}); // Safe sign extension.
```

Note that an operation is only considered signed if all of the operands are
signed, and that literal values can be specified as signed, for example:
`2'sb11` is -1 in 2 bits.

[arithmetic-gotcha]: http://www.sutherland-hdl.com/papers/2006-SNUG-Boston_standard_gotchas_presentation.pdf

**Avoid splitting arithmetic** between statements or modules. This facilitates
optimisation during synthesis, for example, to choose or generate an optimised
adder implementation for the given set of operands and carry ins/outs. Instead of:
```
logic [3:0] a, b, c;
logic [4:0] int_sum, sum;
int_sum = a + b;
{unused_co, sum} = int_sum + {1'b0, c};
```

All of the arithmetic contributing to `sum` can be written in a single
expression:
```
{unused_co, sum} = a + b + c;
```

<a name="code-structure"></a>
## Code structure

**Place parameters and variables at the top of their containing scope.** Doing
this gives and overview of the state and complexity of a block, particularly a
module. Declarations of combinatorial and sequential nets should be separated
into different sections for clarity. Note also that variables declared in
unnamed scopes are not accessible via the design hierarchy and will not appear
in wave viewers. To separate a module into sections without making signals
inaccessible, a named scope can be introduced. The following example of a
ripple-carry adder with registered outputs gives an idea of this style of
structuring:

```
module ripple_carry_adder
  #(parameter p_WIDTH = 8)
  ( input  logic               i_clk,
    input  logic               i_rst,
    input  logic [p_WIDTH-1:0] i_op1,
    input  logic [p_WIDTH-1:0] i_op2,
    output logic               o_co,
    output logic [p_WIDTH-1:0] o_sum );

  // Wires.
  logic [p_WIDTH-1:0] carry;
  // Registers.
  logic [p_WIDTH-1:0] sum_q;
  logic               co_q;
  // Variables.
  genvar i;

  assign carry[0] = 1'b0;
  assign {o_co, o_sum} = {co_q, sum_q};

  // Named generate block for per-bit continuous assignments.
  for (i = 0; i < p_WIDTH; i = i + 1) begin: bit
    assign {carry[i+1], sum[i]} = i_op1[i] + i_op2[i] + carry[i];
  end

  always_ff @(posedge i_clk or posedge i_rst)
    if (i_rst) begin
      sum_q <= {p_WIDTH{1'b0}};
      co_q  <= 1'b0;
    end else begin
      sum_q <= sum;
      co_q  <= carry[p_WIDTH-1];
    end

endmodule
```

**Use `.*` and `.name()` syntax to simplify port lists in module
instantiations.** This reduces the amount of boilerplate code and thus the
scope for typing or copy-paste errors. `.*` also provides additional checks: it
requires all nets be connected, it requires all nets to be the same size and it
prevents implicit nets from being inferred. Named connections with `.name()` can
be used to add specific exceptions. For example:

```
module foo (input logic i_clk,
            input logic i_rst,
            input logic in,
            output logic out);
  ...
endmodule

u_module foo (.*,
              .in(in),
              .out(out));
```

**Avoid logic in module instantiations.** By instantiating a module with a set
of named signals, it is easier to inspect the port hookups and the widths of
the signals for correctness.

<a name="signal-naming"></a>
## Signal naming

A strict approach to naming should be taken to make it easier to understand and
navigate a design:

**To make clear their relationship to the structure of a module**. Prefixes and
suffices can denote, for example, whether a signal is an input or output, the
pipeline stage it corresponds to and whether it is driven by logic or directly
from a flip-flop. The exact naming convention will be tailored to a project,
but here are some examples:

```
i_p0_operand     // Input into pipeline stage 0.
p1_state         // A current state of a state machine.
p1_state_ns      // The next state.
state_clk        // A clock signal.
m1_sum_co_unused // An unused carryout bit from an addition.
m2_result_ff     // A registered result, driven by a flip-flop.
o_x4_state       // An output signal driven from stage x4.
```

**To allow simple sorting and searching in wave viewer**. By using common
prefixes for related signals, sorting will place them together. Similarly,
common substrings are useful to filter a subset of signals over, for example to
select a set of registers or similar signals different in pipeline stages.

**To be flattened sensibly by downstream tools**. It is typical for synthesis
to flatten the hierarchical structure of a Verilog design. Consequently
symbols names are derived from their place in the module hierarchy. A suitable
naming scheme really only requires consistency across a design. As an example,
a flip-flop clock pin might be named
`u_toplevel_u_submodule_p0_signal_q_reg_17_/CK` corresponding to the register
`u_toplevel/u_submodule/p0_signal_q[17]`.

<a name="summary"></a>
## Summary

Verilog is a large language with features supporting different purposes. It is
used as a standard in hardware design but its specification does not define a
synthesizable subset. Although there is a general consensus on which features
can be used for synthesis, the fine details are determined by the particular
EDA tooling flow used by a design team. Verilog is consequently used in a
conservative way for specifying synthesizable designs. The rules and rationale
given in this note outline some of the important aspects of a coding style for
hardware design. There are many more details of Verilog's features that are
relevant; the references below are a good place to find out more.

<a name="refs"></a>
## References/further reading

- IEEE Standard for SystemVerilog (IEEE 1800-2012 and 1800-2017).
- [Sutherland HDL papers](http://www.sutherland-hdl.com/papers.html) on Verilog, in particular:
    * Stuart Sutherland and Don Mills, Standard gotchas subtleties in the
      Verilog and SystemVerilog standards that every engineer should know. SNUG 2006.
      ([PDF](http://www.sutherland-hdl.com/papers/2006-SNUG-Boston_standard_gotchas_paper.pdf))
    * Stuart Sutherland, A Proposal for a Standard Synthesizable SystemVerilog Subset. DVCon 2006.
      ([PDF](http://www.sutherland-hdl.com/papers/2006-DVCon_SystemVerilog_synthesis_subset_paper.pdf))
    * Stuart Sutherland and Don Mills, Synthesizing SystemVerilog: Busting the
      myth that SystemVerilog is only for verification, SNUG 2013.
      ([PDF](http://www.sutherland-hdl.com/papers/2013-SNUG-SV_Synthesizable-SystemVerilog_paper.pdf)).
    * Stuart Sutherland and Don Mills, Can my synthesis compiler do that? What ASIC
      and FPGA synthesis compilers support in the SystemVerilog-2012 standard, DVCon 2014
      ([PDF](http://www.sutherland-hdl.com/papers/2014-DVCon_ASIC-FPGA_SV_Synthesis_paper.pdf)).
- SystemVerilog's priority & unique - A Solution to Verilog's "full_case" & "parallel_case" Evil Twins!,
  Clifford E. Cummings, SNUG 2005
  ([PDF](http://www.sunburst-design.com/papers/CummingsSNUG2005Israel_SystemVerilog_UniquePriority.pdf)).
- Verilog HDL Coding, Semiconductor Reuse Standard, Freescale Semiconductor
  ([PDF](https://people.ece.cornell.edu/land/courses/ece5760/Verilog/FreescaleVerilog.pdf)).
- Complex Digital Systems, Synthesis, MIT OCW, 2005 (presentation slides,
  ([PDF](https://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-884-complex-digital-systems-spring-2005/lecture-notes/l05_synthesis.pdf)).
