# Extractor Template

This code is intended to be used as a template for writing additional plot-level, RGB-based, phenomic extractors for the Drone Processing Pipeline.

## Overview

This templated code has been developed as an effort to make writing new extractors, and keeping them up to date, easier.
By isolating the algorithm code from the rest of the infrastructure needed by an extractor we've been able to reduce the lead time for producing a working extractor.

The following steps are needed when using this template. Note that all the sections referenced can be found below

1. Make a copy of this repository as outlined in the "Getting Started" section
2. Fill in the algorithm() function as outlined in the "Adding Your Algorithm" section
3. Create your docker container and make it available as described in the "Docker Container" section
4. Download, register, and run your extractor as outlined in the "Running Your Extractor" section

## Getting Started

To get started 
