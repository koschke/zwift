# zwift
A Python script generating a Zwift workout file based on a simple textual workout specification

## What does this script do?

This script generates a [Zwift](https://zwift.com/) workout file taking a simple and concise textual workout specification. The [Zwift](https://zwift.com/) workout file can be read in [Zwift](https://zwift.com/) to control your smart trainer during a workout.

## Why using this script?

The Zwift workout editor allows one to create a customized workout and works fine for simple workouts. Yet, it has limitations. First, the intervals you can create with the editor have only two different stages: low power and high power. Second, copy and pasting and editing in general to create a workout can be cumbersome. As an alternative to the Zwift workout editor, you can also create those Zwift workout files yourself using a simple text editor. In fact, the Zwift workout file can be read by humans and machines. It is textual [XML](https://en.wikipedia.org/wiki/XML)-based format that you can write yourself. Unfortunately, it is a bit verbose and may be difficult to understand and write by people with litle or no experience in computer science.


Third, if you receive a workout description from a trainer or training plan that uses absolute power numbers, you need to calula
