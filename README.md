# zwift
A Python script generating a Zwift workout file based on a simple textual workout specification

## What does this script do?

This script generates a [Zwift](https://zwift.com/) workout file taking a simple and concise textual workout specification. The [Zwift](https://zwift.com/) workout file can be read in [Zwift](https://zwift.com/) to control your smart trainer during a workout.

## Why using this script?

The Zwift workout editor allows one to create a customized workout and works fine for simple workouts. Yet, it has limitations. First, the intervals you can create with the editor have only two different stages: low power and high power. Second, copy and pasting and editing in general to create a workout can be cumbersome. As an alternative to the Zwift workout editor, you can also create those Zwift workout files yourself using a simple text editor. In fact, the Zwift workout file can be read by humans and machines. It is a textual [XML](https://en.wikipedia.org/wiki/XML)-based format that you can write yourself. Unfortunately, it is a bit verbose and may be difficult to understand and write by people with litle or no experience in computer science. What makes it even harder is that the Zwift workout file format is not really documented. There is [a very useful attempt to describe it](https://github.com/h4l/zwift-workout-file-reference/blob/master/zwift_workout_file_tag_reference.md), but there is no offical and reliable documentation from Zwift.

## Why I developed this script

I am receiving my bike-workout description from my trainer in a textual description stating the target power in absolute terms. I didn't like to use the Zwift editor for the above reasons. So I turned the textual description I got from my trainer into a Zwift workout using a text editor. Yet, I had to make calculations for convering the absolute power data into power data relative to my FTP value because absolute power data cannot be used in Zwift workout files. Likewise, I had to convert time data given in minutes into seconds because only seconds can be used in Zwift workout files. Yes, doing these calculations is simple but it takes time. Doing that over and over is a waste of time and often I noticed errors only when I started the workout in Zwift. One day I had enough and decided to write a program to automate this task.


