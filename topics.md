# Practical Microservices
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
    3. data consistency and types, API design
        * I like untyped languages, whats up w types in swagger, thrift, protobuf?
        * I like typed languages, but compiler cant help detect broken / incompatible network interfaces
        * DB transactions are nontrivial to implement generically in RPC, easier to write specialized functions
        * Multiple favorite encoding options (thrift, json, protobuf, msgpack, xml, ...) how to choose?
        * rest vs RPC APIs
    4. dealing with the network
        * Cant trust other services to behave sanely (eg: must do ratelimiting).
        * Service discovery is a new problem (this was a non-issue for monolithical code)
        * Network issues (and problems from trying to mask them) require new solutions (eg: circuit breaking).
        * Refactoring is much harder (network APIs in use are hard to change).
        * API versioning tedious, requires significant administration and communication of roadmap.
        * Multiple models (eg: several competing ideas on whats a User record).
    5. Deployment
        * trying it out locally
        * deployment strategies (traditional, red-green, immutable infrastructure)
        * hosted servers (ftp)
        * ec2
            * s3 deploy
            * orchestrated (placement)
        * deploy-time dependency checking
        * lifecycle: when is the app ready, when can it be killed?
    6. Monitoring:
        * collecting logs (log sink, scribe, etc).
        * analyzing logs, defining alerts
        * counters, stats (eg RPC)
        * whats useful to see on a dashbaord during an outage?
    7. Software Architecture:
        * stateful vs stateless services
        * scaling horizontally vs vertically
        * supervisors, supervisor trees and strategies
        * how to map state storage requirements
        * caches and invalidation
