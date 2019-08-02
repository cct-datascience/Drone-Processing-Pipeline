# Extractor Template
<img src="./resources/drone-pipeline.png" width="100" />

This code is intended to be used as a template for writing additional plot-level, RGB-based, phenomic extractors for the Drone Processing Pipeline.

Knowledge of the Python language and Docker containers are necessary for using this template.

## Overview

This templated code has been developed as an effort to make writing new extractors, and keeping them up to date, easier.
By isolating the algorithm code from the rest of the infrastructure needed by an extractor we've been able to reduce the lead time for producing a working extractor.

In this document we will be referring to a fictional extractor name of 'ruby'.
This name is used for illustrative purposes only and you should use your own extractor name.

The following steps are needed when using this template. Note that all the sections referenced can be found below.

1. Make a copy of this repository as outlined in the [Getting Started](#starting) section
2. Fill in the configuration.py file and create the needed files as described in the [Configuration](#configuration) section
3. Fill in the calculate() function as outlined in the [Adding Your Algorithm](#algorithm) section 
4. Create your Docker image and make it available as outined in the [Making a Docker Image](#docker) section

## Getting Started <a name="starting"/>

Before you start, make sure to have your own respoitory in which you can make your changes.

At this point there are two main approaches that can be taken; clone or submodule the template code.
Another option is to download a .zip of the repository and unzip it into your project; we will not be covering this approach.
If you are using [GitHub](https://github.com) you can clone the [repository](https://github.com/az-digitalag/Drone-Processing-Pipeline.git) as a [template](https://help.github.com/en/articles/creating-a-repository-from-a-template).

**Clone**
The advantage to cloning is that you have a stable copy of the code to change as you want.
The disadvantage of cloning is that when the template gets updated you will need to manually merge any changes.

**Submodule**
The advantage of using a submodule is that it's easy to update to the latest template code through a single command.
The disadvantage of using a submodule is that the file system layout of a project is more complex.

At this time, only cloning is documented.
We are hoping to document submodules in the near future.

To clone the template, open a command window and change to the location of your repository on disk (for example, `cd ~/my-repo`).
Next use git to clone the template project by running `git clone https://github.com/az-digitalag/Drone-Processing-Pipeline.git extractor-ruby`.

Unfortunately git doesn't allow you to checkout/branch a subfolder.
It's recommended that you perform the following clean-up steps:
1. Remove any file from the *extractor-ruby* folder
2. Remove all folders **except for** the `extractor-template` folder
3. Move the contents of the *extractor-template* folder to the current folder (should be the one named "extractor-ruby" in this example)
4. Finally, delete the now-empty "extractor-template" folder

At this time you may want to check your changes into source control.
Note that after running the [Generate Files](#generate) step we recommend deleting a file.
Depending upon your comfort level with the source control you use, you may want to wait until after that step to check files in.

## Configuration <a name="configuration"/>

There are two steps needed for configuration:
1. Update the file named "configuration.py" with your values
2. Run the "do_config.py" script - this requires Python to be installed

### Edit configuration.py <a name="configuration_py"/>

There are several fields that need to be filled in with values that are meaningful for your extractor.

**EXTRACTOR_NAME**

This is the name that your extractor will be known by.
The best choice is to pick a name that is descriptive of your algorithm, hasn't been used before, and isn't too long.
Sometimes your best name has been used already.
When this is the case, adding a short identifier can help.
For example, using your initials or adding a an adjective can help.

All alphanumeric characters are allowed, as are underscores.
The name you choose will be converted to lowercase in the code.
This means that "MyNiftyExtractor" is considered the same as "mynifyextractor" and "mYnIFTYeXTRACTOR" 

**VERSION**

This is the reported version of your extractor.
It is important to increment this number every time you release an updated extractor.

**DESCRIPTION**

A very short description of what your extractor does.

**AUTHOR_NAME**

This would be your name or the name of the principal contact.
The value entered here is used as part of the created docker container information as well as when the extractor is registered.

**AUTHOR_EMAIL**

This is the email address to use as a contact point.
It is used in conjunction with the AUTHOR_NAME field

**REPOSITORY**

Specify the full URL to your code repository.

### Generate files <a name="generate"/>

There are two principal files that are configuration based.
The `do_config.py` script generates these files for you based upon the values entered into the [configuration.py](#configuration_py) file.

Two files are generated by the script:
* extractor_info.json: contains JSONLD information used to register the extractor
* Dockerfile: the commands to build a docker image of your extractor

To generate these files, first make sure your configuration.py file is up to date, then do the following:
1. Open a command shell and change to the folder containing the `do_config.py` script, or use a file browser to browse to the folder
2. Run the script by entering the following command in the command shell `./do_config.py`, or by running the file from the file browser (usually by double-clicking the name).

If you can't run the script, make sure you have Python installed.
Alternatively, with the command shell, you might need to specify the python version to run, as shown with the following command: `python3 ./do_config.py`.

If the script encounters a problem, an error is reported.
Correct the caause of the reported error and try running the command again.

Once you are satisfied with the results you can delete the *do_config.py\** files.

This is another good point to save your files to source control.

## Adding Your Algorithm <a name="algorithm"/>

Your algorithm will reside in a separate file named `extractor.py`, in a function named `calculate`.
The *extractor.py* file copied from source control (as described in [Getting Started](#starting)) contains the outline of this function.
The *calculate* function receives a numpy array of RGB data representing a single plot.

You will need to modify *extractor.py* to import the modules you need and perform the actions for your algorithm.

The calling code expects a single value to be returned that can be represented as text.
This can be a single string, a number value, a JSON object, or something else.
It's important that the value returned has the accuracy needed.
For example, if only two decimal places are needed for a real number, it would be best to return a string that exactly represents the desired value.

## Making a Docker Image <a name="docker"/>

In the [Configuration](#configuration) section the `do_config.py` script generated a file named "Dockerfile".
This file has the basic configuration needed to build an extractor as a Docker container.

Before trying to build the Docker container, you should review the *Dockerfile* file for additional installation steps.
If more installation steps are needed, they can be added to the file as needed.

Once the *Dockerfile* file is ready, run the `docker build` command to generate your image.
Refer to the Docker documentation and the `docker` application command line help for additional information on how to build an image.

Once your extractor is built, it's recommended that it's placed on [Docker Hub](https://hub.docker.com/) or on a similar repository.
