# Extractor Template

This code is intended to be used as a template for writing additional plot-level, RGB-based, phenomic extractors for the Drone Processing Pipeline.

## Overview

This templated code has been developed as an effort to make writing new extractors, and keeping them up to date, easier.
By isolating the algorithm code from the rest of the infrastructure needed by an extractor we've been able to reduce the lead time for producing a working extractor.

In this document we will be referring to a fictional extractor name of 'ruby'.
This name is used for illustrative purposes only and you should use your own extractor name.

The following steps are needed when using this template. Note that all the sections referenced can be found below.

1. Make a copy of this repository as outlined in the "Getting Started" section
2. Fill in the algorithm() function as outlined in the "Adding Your Algorithm" section
3. Create your docker container and make it available as described in the "Docker Container" section
4. Download, register, and run your extractor as outlined in the "Running Your Extractor" section

## Getting Started

Before you start, make sure to have your own respoitory in which you can make your changes.

At this point there are two main approaches that can be taken; clone or submodule the template code.
Another option is to download a .zip of the repository and unzip it into your project; we will not be covering this approach.

**Clone**
The advantage to cloning is that you have a stable copy of the code to change as you want.
The disadvantage of cloning is that when the template gets updated you will need to manually merge any changes.

**Submodule**
The advantage of using a submodule is that it's easy to update to the latest template code through a single command.
The disadvantage of using a submodule is that the file system layout of a project is more complex.

At this time, only cloning is supported.
We are hoping to support submodules in the near future.

To clone the template, open a command window and change to the location of your repository on disk (for example, `cd ~/my_nifty_extractor`).
Next use git to clone the template project by running `git clone https://github.com/az-digitalag/Drone-Processing-Pipeline.git`.
Rename the `extractor-template` folder to something meaningful, such as "extractor-ruby".

At this time you should check your changes into source control.

## Adding Your Algorithm