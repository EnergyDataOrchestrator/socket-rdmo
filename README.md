# socket-rdmo
An ontology-aware bridge for the Regimo Orchestrator. Connects the Kafka energy data bus to the Research Data Management Organiser (RDMO) for automated metadata documentation.

## Overview
The `socket-rdmo` is a specialised microservice within the **Regimo** ecosystem designed to facilitate communication between the Energy Data Orchestrator and the **RDMO (Research Data Management Organiser)** platform. It ensures that data processed by the orchestrator is correctly documented and aligned with Research Data Management (RDM) plans.

## Core Functionality
As an **ontology-aware socket**, this component listens to specific topics on the Kafka bus and maps semantic energy data to RDMO's metadata structures. This automation supports the KIT research workflow by providing:

* **Automated Documentation:** Synchronising real-time experiment metadata from the energy bus directly into RDMO.
* **Semantic Translation:** Converting Regimo-ontology-based data points into RDM-compliant descriptors.
* **Lifecycle Management:** Ensuring that energy data streams are associated with the correct project IDs and data management protocols defined in RDMO.



[Image of research data management lifecycle]


## Integration Architecture
This socket functions as a "bridge" component within the EDO hierarchy:

1. **Input:** Consumes ontology-tagged messages from the Kafka bus.
2. **Logic:** Processes data through the `regimo-ontology` definitions to identify relevant RDM metadata.
3. **Output:** Interacts with the RDMO API to update or query project information.



## Repository Contents
* `src/`: Implementation of the Kafka consumer and RDMO API client.
* `mapping/`: Configuration files defining the relationship between Regimo ontology classes and RDMO attributes.
* `docker/`: Containerisation files for deployment within the `edo` orchestration environment.