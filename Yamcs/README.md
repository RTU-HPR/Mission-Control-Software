# Yamcs QuickStart

This folder holds the source code to start the Yamcs application.


## Prerequisites

* Java 11+
* Linux x64/aarch64, macOS x64, or Windows x64

A copy of Maven 3.1+ is also required, however this gets automatically downloaded an installed by using the `./mvnw` shell script as detailed below.

Note that Yamcs does not currently support running on Apple M1 or M2. We hope to address this soon.


## Running Yamcs

Here are some commands to get things started:

Compile this project:

    ./mvnw compile

Start Yamcs on localhost:

    ./mvnw yamcs:run

Same as yamcs:run, but allows a debugger to attach at port 7896:

    ./mvnw yamcs:debug
    
Delete all generated outputs and start over:

    ./mvnw clean

This will also delete Yamcs data. Change the `dataDir` property in `yamcs.yaml` to another location on your file system if you don't want that.


## Bundling

Running through Maven is useful during development, but it is not recommended for production environments. Instead bundle up your Yamcs application in a tar.gz file:

    ./mvnw package
