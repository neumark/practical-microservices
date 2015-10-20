# Practical Microservices

Microservices have been a trendy topic among system architects and software engineers for years now.
To generalize, *a microservice architecture is composed of many simple services or components connected in a potentially complicated topology.* This is the exact opposite of a monolithical application, which has few components (often just one), which in turn are rather complex. Its intuitive that it is easier to reason about the properties of a system containing simple components than one with unpredictably complicated parts. The hype around microservices is based on the assumption that this remains true when the number of simple components and the complexity of the network which connects them increases.

## Introduction
If everybody's been talking about microservices for years now, what can possibly be left to say? Several key industry players, such as Netflix and Twitter have shared extensive details about their architecture and open sourced much of the code required to implement a system similar to theirs (apart from the business logic).

Most people wanting to implement microservices in their own organization overlook the fact that as with any existing technology, these open source libraries are built on certain tradeoffs and assumptions. For example, Twitter's business relies on building a product which has very low latency. This concern is deeply ingrained in the technical decisions made in the Finagle codebase. Many of the complex optimizations within are unnecessary for a company which has a different business model in which latency is not a primary concern. Is Finagle high-quality software? Absolutely. Is it the right tool for you? That depends.

When a monolithical application is broken up into a set of simple services, important properties of the original design are often lost. Far too often, the new system is more difficult to debug, its performance is harder to measure, and the local development environment no longer resembles production. These cases invariably lead to disillusionment with the microservice concept (and typically the individuals who introduced it). A better understanding of the typical pitfalls and potential solutions could greatly decrease the frequency and the magnitude of these unhappy project outcomes.

The goal of this tutorial is to provide a simple example of a microservice architecture which can be used as a simulator so architectural problems and their solutions can be seen without having to invest in splitting up or rewriting a real application.

## Advantages of microservices
As the number of companies developing and operating web-based services used by millions of users grows, so does the group of engineers who are frantically searching for solutions to the following problems:
* How can an organization enforce loose coupling of components without introducing more process?
* How can one avoid re-implementing lots of code upon the introduction of a new language or framework?
* How can the responsibility for parts of an application or service be more well-defined?
* How can applications scale horizontally?
* How can systems handle failure without losing or corrupting state?
* How can one isolate and manage technical debt without making risky changes in production?
* How can breaking API changes be introduced without downtime?

The above is an incomplete list of hard problems that many believe are solved by transitioning to a microservice architecture. In part, this is due to the fact that the term *microservice* has become a buzzword including best practices not necessarily related to the original definition of the word, such as using several small source code repositories instead of one large combined repo.

This tutorial will focus solely on the development and operation of a system made of several simple services. Topics like source code management, build systems and distribution of responsibilities -while important- are outside its scope.

In light of this, the primary advantages of the microservice architecture boil down to the following:
* Language and stack-agnostic interfaces.
* Improved separation between stateful and stateless parts of the system.
* Easier scaling for the stateless parts.
* Potentially simple stateful parts, making them easier to operate reliably.

These advantages are important, but they are not automatically realised upon dividing an application into several services. Below are some of the disadvantages typically associated with systems composed of a large number of simple services. Unfortunately, these is no simple recipe to follow which will prevent these issues:
* Testing is generally more difficult (unit testing in particular).
* Local development and debugging ca be painful (the latter is sometimes impossible).
* Boilerplate code providing similar functionality with slight modifications can appear in services.
* Network effects can lead to previously unseen problems (for example, clients killing an overloaded service by retrying requests when it is slow to respond).

## Microservices are not a technology
Microservices are a set of design principles and a collection of best practices. Depending on the business needs of an organization, different subsets of these principles and practices apply. Unlike a programming language or a framework, using microservices is not a binary state. There is no single criterium which defines whether or not a particular system architecture qualifies as a microservice. In this tutorial, the transition from monolithic web app to a set of simpler services follows a sequence of steps. The advantages of this sequence will be highlighted, but there are other possible paths with different pros and cons, which -depending on your business needs- may be more suitable for you. The most important thing is to always make changes to a system which at least don't signficiantly degrade important properties of the product. What they are depends on the specific situation. Some examples are debuggability, brevity of tests and  performance. Typically, a monolithical application about to be carved into microservices will already have these properties; the goal is not to lose them along the way.

## About the tutorial code
The tutorial is based on a fictional company, *FibInc*, and their product *FibPro*. FibPro is a webservice which calculates fibonacci numbers. In it's earliest incarnation TODO:link-to-branch, it is a single service written in python. Defining moments of the transition to a microservice architecture have separate branches in this repository. All bugfixes and feedback related to the code or this text is welcome! Send issues, pull requests and email!

## FibPro setup
After cloning the repository, running `./bin/setup.sh` should install all the python dependencies of the demo. In addition, `haproxy`, `screen` and `watch` are used. Please install them manually. The text of this tutorial and the code assumes `fibpro.com` is an alias to localhost. To add this alias, add the following to `/etc/hosts`:

```
127.0.0.1   fibpro.com
```

To run the demo, simply run `./bin/start.sh`. FibPro can be terminated by pressing *Control-F*. It is possible that some services will remain running after the screen session has terminated. Unfortunately in this case these processes must be killed by hand. The brave can do this by running `killall python`.

## In the beginning was the monolith
Much like in 2001: Space Odessey, the story begins with the monolith. In FibPro's case, the monolith includes basic user management in addition to fibonacci calculation TODO:link-to-branch.
