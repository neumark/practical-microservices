1. Microservice motives
    * Individual responsibility
    * Code modularity
    * Simpler services, less technical debt
    * Better horizontal scaling by separating stateful and stateless parts of system
    * Breaking free of the single language / single VM constraint
    * Increased reliability (minimizing SPOF)
    * Better suited to containerized, EC2-ifid cloud environment
    * lowers barrier of entry for replacing parts of system (just throw out the simple service).
    * all the cool kids are doing it (bad motive)
1. Microservice problems
    1. request tracing, analyizing
        * Stack traces are meaningless (HTTP 500 errors)
        * Its hard to match external requests with their resulting internal requests (thus analyze traffic flow).
        * Measuring performance is hard
        * Interactive debugging not possible across network APIs
    2. environments and testing
        * Setting up local devenv is tedious
        * Unit testing code full of RPC calls difficult
        * Environment difficult to set up for acceptanct tests / functional tests
        * Complexity of running local, prod, test environments (possibly more)
    3. dealing with network APIs
        * I like untyped languages, whats up w types in swagger, thrift, protobuf?
        * I like typed languages, but compiler cant help detect broken / incompatible network interfaces
        * Cant trust other services to behave sanely (eg: must do ratelimiting).
        * Service discovery is a new problem (this was a non-issue for monolithical code)
        * Network issues (and problems from trying to mask them) require new solutions (eg: circuit breaking).
        * Refactoring is much harder (network APIs in use are hard to change).
        * API versioning tedious, requires significant administration and communication of roadmap.
        * Multiple models (eg: several competing ideas on whats a User record).
