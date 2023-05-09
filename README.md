# zwift.py
A Python script generating a Zwift workout file based on a simple textual workout specification

## What does this script do?

This script generates a [Zwift](https://zwift.com/) workout file taking a simple and concise textual workout specification. The [Zwift](https://zwift.com/) workout file can be read in [Zwift](https://zwift.com/) to control your smart trainer during a workout.

## On which operating systems will this script run?

The script runs on Windows, macOS, and Linux. Technically, it runs on every platform for which a _Python_ interpreter is available ([see below](#what-do-i-need-to-install-on-my-computer-to-use-the-script)).

## Is this script for free?

Yes, absolutely.

## Why using this script?

The Zwift workout editor allows one to create a customized workout and works fine for simple workouts. Yet, it has limitations. First, the intervals you can create with the editor have only two different stages: low power and high power. Second, copying and pasting and editing in general to create a workout can be cumbersome. 

As an alternative to the Zwift workout editor, you can also create those Zwift workout files yourself using a simple text editor. In fact, the Zwift workout file can be read not only by machines but also humans. It is a textual [XML](https://en.wikipedia.org/wiki/XML)-based format that you can write yourself. Unfortunately, XML is rather verbose and may be difficult to understand and write by people with little or no experience in computer science. What makes it even harder is that the Zwift workout file format is not really documented. There is [a very useful attempt to describe it](https://github.com/h4l/zwift-workout-file-reference/blob/master/zwift_workout_file_tag_reference.md), but there is no offical and reliable documentation offered by Zwift.

## Why did I develop this script?

I am receiving my bike-workout descriptions from my trainer in a textual description stating the target power in absolute terms. I didn't like to use the Zwift editor for the above reasons. So I turned the textual description I got from my trainer into a Zwift workout using a text editor. Yet, I had to make calculations for converting the absolute power data into power data given by my trainer into values relative to my functional threshold power (FTP) because absolute power data cannot be used in Zwift workout files. Likewise, I had to convert time data given in minutes or hours into seconds because only seconds can be used in Zwift workout files. Yes, doing these calculations is simple - but it does take time. Doing that over and over is a waste of time and often I noticed errors only when I started the workout in Zwift. One day I had enough and decided to write this script to automate this task.

## How does the workout specification look like?

We will first explain the syntax of a workout specification by examples. After that, a formal definition of the syntax will follow that describes precisely how a valid workout specification must look like.

### The syntax explained by examples.

The workout specification is textual, more concise and much simpler than a Zwift workout file. The most simple kind of workout where you would write 200 watts for 30 minutes would look like this:

```
30m@200w | 250w
```

Isn't that simple? The first part `30m@200w` specifies a duration of 30 minutes at 200 watts. The second part `| 250w` declares your FTP value, which would be 250 watts in this example. The FTP value in a workout specification should match the FTP value that you set in Zwift. For the unit of watts, you can use `w` or `W`. Power data must always be integer values, that is, you must not use a decimal point. For instance, `100.5w` is invalid.

The blanks in the workout specifications have no meaning and are only a matter of your taste about readability. You could as well write:

```
30 m @ 200 w|250 w
```

If you want to start your workout with a warm-up and cool-down phase, you can specify power ranges. Let's assume you want to start by gradually increasing your power from 100 watts to 190 watts over 10 minutes and after your main set of 30 minutes at 200 watts you want to decrease your power from 190 watts down to 150 watts in 5 minutes. You could specify this workout as follows:

```
10m@100w-190w + 30m@200w + 5m@190w-150w| 250w
```

A power range is defined by starting and ending power separated by a `-`, e.g., `100w-190w` increases from 100 watts to 190 watts. Note that you need to specify the watt unit (`w` or `W`) for both the starting and ending power. If the starting power is lower than the ending power, as in `190w-150w`, power will decrease over the specified duration.

As you can see in this example, too, different sets are separated by `+`.

Now let's assume we want a classic 30/30 interval with 9 repeats instead of the steady 200 watts over 30 minutes. A 30/30 interval is an effort with 30 seconds at high power, let's say 290 watts, followed by a 30-second rest at low power, let's say 100 watts. This can be specified as follows:

```
10m@100w-190w + 9*(30s@290w + 30s@100w) + 5m@190w-150w| 250w
```

Note the factor `9` and the symbol `*` in front of the expression in the brackets. This means that the set described in the brackets should be repeated nine times. Note also that you can specify time not only in minutes using either `m` or `M`, but also in seconds (either `s` or `S`) as well as hours (either `h` or `H`). Times can also be given as a decimal number. The following durations are all the same: 0.5h = 0.5H = 30m = 30M = 1800s = 1800S. Yet, durations will always be rounded to integer seconds, that is, although you can write `1.3s` or `1.6s`, these numbers will be rounded in the generated Zwift workout file to `1s` or `2s`, respectively.

Unlike in the Zwift workout editor, you can have intervals with more than two sets and even nested intervals as the following example shows:

```
2*(5m@180w + 9*(10s@300w + 30s@290w + 30s@100w))| 250w
```

This workout consists of two repeats of 5 minutes at 180 watts, followed by a nested interval of nine repeats of a variation of the former 30/30 efforts. The variation starts a little harder with 300 watts for 10 seconds and then eases back to the 290 watts for the remaining 20 seconds before the 30-second rest begins.

This workout is equivalent to:

```
5m@180w + 9*(10s@300w + 20s@290w + 30s@100w) + 5m@180w + 9*(10s@300w + 30s@290w + 30s@100w)| 250w
```

If you want to have a free ride in your workout, you can use `_` instead of a concrete wattage or wattage ramp. To have a 30-minute free ride with no power obligation, you can write:

```
30m@_ | 250w
```

Note that there is no `w` or `W` after the `_`.  Note also that you still need to specify your FTP even though this workout example consists of only a single free ride where an FTP value does not really matter. Yet, you would hardly create a Zwift workout consisting of only free rides, would you? And if there is a concrete power specification, the absolute number must be turned into a relative value for the said technical limitation of the Zwift workout format.

### A precise definition of the syntax for workout specifications

You can skip this section if you are happy with the description by examples given above. However, if the script detects a syntax error in your workout specification and you do not understand what is wrong with it, the following formal definition of the syntax of workout specification may be useful.

Workout specifications are a kind of (artifical) language to be understood by humans and computers. While humans are typically good at tolerating language errors, computers are generally more stubborn in that regard. If `zwift.py` does not understand your workout specification, how could it generate a Zwift workout file for it? 

In computer science, syntax is often defined by [Extended Backus–Naur form, or short: EBNF](https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form). EBNF is a notation by which the syntax of a textual input to a computer program can be defined. In the following, the syntax a workout specification must conform to will be described using EBNF. I will explain the syntax rules for our workout specifications and EBNF in the following. Have no fear, it is not that difficult. A more complete description of EBNF can be found [here](https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form). A footnote to the pedants: I am not using the semicolon at the end of a rule, which would be required according to EBNF.

Let us start with the first syntax rule:

```
  Workout = Stages FTP
```

The name `Workout` on the left-hand side of `=` is the name of a syntax rule. Rule names are also known as _Non-Terminals_. The right-hand side of `=` defines the rule. Here we have `Stages` and `FTP`. Both are again non-terminals, that is, other rules. The right-hand side states that any workout description consists of two parts: first, the stages of a workout and then a declaration of the FTP value. Let us first take a look at the rule for `FTP`, simply because it is simpler.

```
FTP = "|" Integer WUnit
```

As you have already seen in the examples above, you declare your FTP value at the end of a workout description after a separating `|`. As you will notice, in the syntax rule, the separator `|` is enclosed in quotes. Everything contained in quotes is interpreted as a terminal in EBNF. While non-terminals define rules that have a right-hand side, terminals stand for themselves, in this case simply for the symbol `|`. You will not find any rule with a terminal on the left-hand side of the rule. They can occur only on the right-hand sides.

After the separator `|` follow an `Integer` and the unit for watts defined by `WUnit`. Integers are natural positive numbers - including 0 - without a period. Their syntax is defined by rule `Integer` as follows:

```
Integer = Digit { Digit }
```

This rule states that an integer must have at least one digit. After that digit an arbitrarily long sequence of additional digits may follow. To represent repitions in EBNF, expressions may be included in curly braces. Everything enclosed by the curly braces may be repeated arbitrarily often, including not at all. 

The rule for single digits is as follows:

```
Digit = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
```

The `|` is used in EBNF to separate alternatives from each other. This rule states that a digit is either a `0` or a `1` or a `2` and so on. Mind the difference between this usage of `|` and our usage `"|"` in one of our syntax rules above. The expression `"|"` is a terminal in a workout specification, while `|` without quotes is an alternation in EBNF enlisting multiple alternative expressions.

Now we have seen all constituents for our `FTP` rule. We now come back to the rule `Stages`:

```
 Stages = Stage { "+" Stage } 
```  

This rule states that `Stages` forms a list of `Stage` (with at least one `Stage`) separated by a `+` symbol. A stage of a workout is described as follows:

```
Stage = (Integer "*" "(" Stages ")") | (Time "@" Watts)
```

Note the EBNF alternation `|` on the right-hand side again. It means that a `Stage` can be either following the syntax `Integer "*" "(" Stages ")"` or the syntax `Time "@" Watts` (the outer braces `(` and `)` are used as a grouping for the two alternatives separated by `|`). The first alternative is intended to define an interval. The `Integer` in front of the `*` symbol is the number of repetitions of the interval. The intervals themselves are described by the expression contained in the braces `(` and `)` (referred to as terminals `"("` and `")"` in the rule). Here we use the non-terminal `Stages` again, that is, again a list of stages separated by `+` is expected, where at least one `Stage` must occur. The attentive reader may have noticed that we could in fact write `3*(5m@200w) | 290w`, that is, there is only one stage in the interval. This would be equivalent to `15m@200w | 290w`. Given the rule for `Integer`and `Digit`, you could even write: `0*(5m@200w) | 290w`, which would result in an empty workout. The zero repetition does not make much sense in this example, but sometimes, a zero may become handy, for instance, for temporarily disabling a repitition in a larger interval. As the first alternative of `Stage` explains, too, the factor of the repititions must come in front of the braces. Accordingly, it would be illegal to write `(5m@200w)*3`.

Now to the other alternative for `Stage`, namely `Time "@" Watts`. This alternative states that first a measure of time and then the target watts separated by `@` must be given. We will first look into `Time`:

```
Time = (Integer | Float) TUnit 
```

In this rule, again alternatives are given (`Integer` or `Float`), but this time the two alternatives are enclosed in braces (again not be confused with our use of braces above - `"("` and `")"` - which are meant to be terminals in workout specifications). The braces `(` and `")"` are used as groupings in EBNF. The expression `(Integer | Float)` means either an `Integer` or `Float` must occur. After these a `TUnit` must follow. We have seen the rule for `Integer` already.  A `Float` consists of two integers separated by a period as follows:

```
Float = Integer "." Integer
```

A `TUnit` is a measure for time as follows (i.e, minutes, seconds, or hours):

```
TUnit = "m" | "M" | "s" | "S" | "h" | "H"
```

The rule `Watts` is intended for defining the target power of a stage.

```
Watts = Integer WUnit [ "-" Integer WUnit ] | "_"
```

As you have seen in the examples above, watts can be specified as a single value such as `300w` or as a range such as `190w - 300w`. This is defined by the first alternative of the right-hand side of rule `Watts`, namely `Integer WUnit [ "-" Integer WUnit ]`. The square brackets `[` and `]` enclose optional expressions, that is, they may or may not occur. The same could be specified as `Integer WUnit | Integer WUnit "-" Integer WUnit`. Beyond any fixed target watt, Zwift also allows you to ride on your own where the smarttrainer would not control the resistance. The other alternative `"_"` states exactly that: free ride. Note that `"_"` is not followed by `WUnit`. `WUnit` is the unit for watts: 

```
WUnit = ("w" | "W")
```

Thus, a free ride `_` must not be followed by either `w` or `W`.

That ends our formal description of workout specification. Thanks for bearing with me. You might find these explanations boring or complicated, but they are good to know when things go wrong and `zwift.py` complains about a syntax error in your workout specification ([see also below](#how-do-I-read-syntax-error-reports)).

## What do I need to install on my computer to use the script?

This script is written in the programming language _Python_. To be able to execute it, you need to install a so called _Python_ interpreter. A _Python_ interpreter is a piece of software that takes a _Python_ program as input and - guess what - interprets its, that is, executes the instructions therein.

You need to install a _Python_ interpreter for _Python_ **version 3.11** on your computer. You can download Python [here](https://www.python.org/downloads/) for a Windows, Linux or a Mac computer at no costs. Make sure that you install version 3.11._X_ where _X_ can be any number (I recommend to install the highest _X_ currently available). 

In addition to _Python_, you need of course to download the script itself that is available [here](https://github.com/koschke/zwift/blob/main/zwift.py). You can copy it to any location on your computer's hard disk. Just remember where. I recommend to copy it to the directory [where the Zwift workouts reside](https://zwiftinsider.com/load-custom-workouts/) (see also below).

That's it. You are good to go.

## How do I run this script?

The script has no graphical user interface. It is intended to be run in a command-line shell, for instance, `cmd` on Windows. I assume most people will use a Windows computer. Hence, I will explain how to open the command-line shell `cmd` on Windows. For Mac or Linux computers, you will find help searching in the Internet. There are many ways to open `cmd` on Windows, the most simple one is: Press Windows+R to open the _Run_ box, where you enter `cmd` and then click _OK_. Now a window with a command-line prompt should open where you can enter your commands. You do not need administrator rights to execute the script.

The following description on how to enter your commands is largely independent from your type of computer (Windows, Mac, or Linux), except maybe for directory separators contained in file-path parameters.

Within a command-line shell, _Python_ programs in general can be started by first stating the path to your _Python_ interpreter, then the name of the _Python_ script to be executed, and then the arguments you want to pass to the executed script. Here is how you would run our script:

```
python zwift.py -w "30m@200w | 250w" -n "My first workout" -o workout.zwo
```

The first item in this command line is the path to the _Python_ interpreter you just installed. If you opted during the installation for adding the _Python_ interpreter to the path where your machine looks up executable programs, you can simply write `python`. If you have not added the _Python_ interpreter to the path of executable programs, you need to specify the full path. On a Windows machine, that could be something like that:

```
"c:\Program Files\Python311\python.exe" zwift.py -w "30m@200w | 250w" -n "My first workout" -o workout.zwo
```

The second item on the command line is our script `zwift.py`. The above command line assumes the script can be found in the current directory. If you copied it to another location on your hard disk, you need again to specify the full path of that location.

After the script's path come the arguments to be passed to the script. The first argument introduced by `-w` is a description of the workout as outlined above. You should always put the workout description you are passing on the command line in quotes. The quotes themselves are not part of the workout specification. Instead, that is the way to pass arguments containing blanks or special symbols. For instance, the symbol `|` has a particular meaning and would be interpreted by the command-line shell and not by the _Python_ interpreter. Always use quotes. Option `-w "30m@200w | 250w"` instructs the script to generate a Zwift workout file for a 30-minute ride at 200 watts with an FTP value of 250 watts. 

Every workout needs a unique name. This name will be shown to you when you want to select one of your custom workouts within Zwift. Note that the filename of a Zwift workout file will not be used as the unique name by Zwift; the name of the workout is instead contained in the Zwift workout file. Hence, it must be passed to `zwift.py` so that it can be put into the output Zwift workout file. You specify the unique name with the option `-n` followed by the name. In the above example, `-n "My first workout"` states that _My first workout_ should be the unique name of the workout. Again you should use quotes, unless your title has no blanks and no special symbols.

The last option in the example above tells `zwift.py` the name of the Zwift workout file that is to be generated. You can select any filename. Note, however, if a file exists already with the chosen name, `zwift.py` will bail out with an error message, because otherwise the existing file would be overridden. If you want to force `zwift.py` to overridde a potentially existing file, you can add option `-f`.

In the example, `-o workout.zwo` specifies that the output should be written into a file named `workout.zwo`. The file extension `.zwo` is mandatory. Zwift will interpret only files with this file extension as files containing workout descriptions. If you do not find your workout in Zwift, the simple reason could be that you did not use the right file extension. Note also that Zwift looks up the workout files only once during start up. If you generate the file while Zwift is already running, you will neither find it in its list of workouts. You would then need to re-start Zwift.

Zwift looks up all its workout files in a particular directory. The path of this directory depends upon your operating system (Windows or MacOS) and your Zwift ID. [This web page](https://zwiftinsider.com/load-custom-workouts/) explains how to determine this directory. I recommend you put the script `zwift.py` in the very same directory so that you do not need to pass more than the filename to `zwift.py` via option `-o`.

Instead of passing a workout description as a parameter to `zwift.py`, you can as well put it in a file and then pass the filename instead via option `-i`. That is particularly handy if you want to have a record of your workout description or if your workout description is very long and you want to break it into multiple lines.

For instance, you can have a file named _myworkout.txt_ with the following content:

```
5m@180w 
+ 9*(10s@300w + 20s@290w + 30s@100w) 
+ 5m@180w 
+ 9*(10s@300w + 30s@290w + 30s@100w)
| 250w
```

Then you can pass this file to `zwift.py` as argument `-i` as follows:

```
python zwift.py -i myworkout.txt -n "My second workout" -o hardworkout.zwo
```

The name of file containing the workout specification follows option `-f`. The name and its file extension can be freely chosen. Note that you need to use either `-w` or `-i`.

Beyond the unique name, you can also add a description to your workout. This description will be shown to you when you select the workout in Zwift. To add a description, use option `-d` followed by the text of the description in quotes. Here is an example:

```
python zwift.py -d "My description" -i myworkout.txt -n "My second workout" -o hardworkout.zwo
```

If you do not use this option, `zwift.py` will add your workout specification as a description.

Finally, if you use option `-h`, `zwift.py` will print its version number and a description on how it can be called and then exits. No Zwift workout file will be generated.


## How do I read syntax error reports?

The script `zwift.py` parses your workout specification from left to right. At the first element of the processed input that must not occur given the input understood so far, it will report a syntax error. 

There are two kinds of syntax errors: (1) the processed workout specification contains a character that must never occur no matter where in a workout specification or (2) an element occurs that may in principle occur in a workout specification but not after the input processed so far.

As an example of the first category, let us assume we have the following invalid workout specification where we wrongly wrote `#` instead of the intended `-`:

```
"10m@180w + 20m@190w#200w | 290w"
```

The syntax report would then look like this:

```
#200w | 290w
Unrecognized character '#'
```

The first line is the remaining part of the workout specification not yet successfully processed. The point where the syntax problem occurs is the first character of that line. The second line describes the problem and tells you that `#` may never occur in a workout specification.

As an example of the second category, let us assume we forget the power unit and wrote:

```
"10m@180w + 20m@190w-200 | 290w"
```

The syntax report would then look like this:

```
| 290 w
w expected
```

Again, the first line is the remaining part of the workout specification not yet processed where the first element is the point of the input not expected given the workout specification successfully processed so far. The second line of the report tells you the possible element or set of elements that would be expected given the current input so as to conform to the formal definition of the syntax for workout specification along with the remaining part of the workout specification not yet processed.

