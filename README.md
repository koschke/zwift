# zwift
A Python script generating a Zwift workout file based on a simple textual workout specification

## What does this script do?

This script generates a [Zwift](https://zwift.com/) workout file taking a simple and concise textual workout specification. The [Zwift](https://zwift.com/) workout file can be read in [Zwift](https://zwift.com/) to control your smart trainer during a workout.

## Why using this script?

The Zwift workout editor allows one to create a customized workout and works fine for simple workouts. Yet, it has limitations. First, the intervals you can create with the editor have only two different stages: low power and high power. Second, copying and pasting and editing in general to create a workout can be cumbersome. 

As an alternative to the Zwift workout editor, you can also create those Zwift workout files yourself using a simple text editor. In fact, the Zwift workout file can be read not only by machines but also humans. It is a textual [XML](https://en.wikipedia.org/wiki/XML)-based format that you can write yourself. Unfortunately, XML is rather verbose and may be difficult to understand and write by people with little or no experience in computer science. What makes it even harder is that the Zwift workout file format is not really documented. There is [a very useful attempt to describe it](https://github.com/h4l/zwift-workout-file-reference/blob/master/zwift_workout_file_tag_reference.md), but there is no offical and reliable documentation offered by Zwift.

## Why I developed this script

I am receiving my bike-workout descriptions from my trainer in a textual description stating the target power in absolute terms. I didn't like to use the Zwift editor for the above reasons. So I turned the textual description I got from my trainer into a Zwift workout using a text editor. Yet, I had to make calculations for converting the absolute power data into power data given by my trainer into values relative to my functional threshold power (FTP) because absolute power data cannot be used in Zwift workout files. Likewise, I had to convert time data given in minutes or hours into seconds because only seconds can be used in Zwift workout files. Yes, doing these calculations is simple - but it does take time. Doing that over and over is a waste of time and often I noticed errors only when I started the workout in Zwift. One day I had enough and decided to write this script to automate this task.

## How does the workout specification look like?

The workout specification is textual, more concise and much simpler than a Zwift workout file. The most simple kind of workout where you would write 200 watts for 30 minutes would look like this:

```
30m@200w | 250w
```

Isn't that simple? The first part `30m@200w` specifies a duration of 30 minutes at 200 watts. The second part `| 250w` declares your FTP value, which would be 250 watts in this example. For the unit of watts, you can use `w` or `W`.

The blanks in the workout specifications have no meaning and are only a matter of your taste about readability. You could as well write:

```
30 m @ 200 w|250 w
```

If you want to start your workout with a warm-up and cool-down phase, you can specify power ranges. Let's assume you want to start by gradually increasing your power from 100 watts to 190 watts over 10 minutes and after your main set of 30 minutes at 200 watts you want to decrease your power from 190 watts down to 150 watts in 5 minutes. You could specify this workout as follows:

```
10m@100w-190w + 30m@200w + 5m@190w-150w| 250w
```

As you can see, differents sets are separated by `+`.

Now let's assume we want a classic 30/30 interval with 9 repeats instead of the steady 200 watts over 30 minutes. A 30/30 interval is an effort with 30 seconds at high power, let's say 290 watts, followed by a 30-second rest at low power, let's say 100 watts. This can be specified as follows:

```
10m@100w-190w + 9*(30s@290 + 30s@100w) + 5m@190w-150w| 250w
```

Note the factor `9` and the symbol `*` in front of the expression in the brackets. This means that the set described in the brackets should be repeated nine times. Note also that you can specify time not only in minutes using either `m` or `M`, but also in seconds (either `s` or `S`) as well as hours (either `h` or `H`). Times can also be given as a decimal number. The following durations are all the same: 0.5h = 0.5H = 30m = 30M = 1800s = 1800S.

Unlike in the Zwift workout editor, you can have intervals with more than two sets and even nested intervals as the following example shows:

```
2*(5m@180w + 9*(10s@300w + 30s@290 + 30s@100w))| 250w
```

This workout consists of two repeats of 5 minutes at 180 watts, followed by a nested interval of nine repeats of a variation of the former 30/30 efforts. The variation starts a little harder with 300 watts for 10 seconds and then eases back to the 290 watts for the remaining 20 seconds before the 30-second rest begins.

This workout is equivalent to:

```
5m@180w + 9*(10s@300w + 20s@290 + 30s@100w) + 5m@180w + 9*(10s@300w + 30s@290 + 30s@100w)| 250w
```

If you want to have a free ride in your workout, you can use `_` instead of a concrete wattage or wattage ramp. To have a 30-minute free ride with no power obligation, you can write:

```
30m@_ | 250w
```

Note that there is no `w` or `W` after the `_`.  Note also that you still need to specify your FTP even though this workout example consists of only a single free ride where an FTP value does not really matter. Yet, you would hardly create a Zwift workout consisting of only free rides, would you? And if there is a concrete power specification, the absolute number must be turned into a relative value for the said technical limitation of the Zwift workout format.
