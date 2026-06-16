```mermaid
 graph TD
    %% Catalog Layer
    Catalog[Catalog: Pigeon: KIT Publication Catalog]

    %% Section Layer
    Catalog --> Sec1[Section: Publication Target]
    Catalog --> Sec2[Section: Instrument Identification]

    %% Page Layer
    Sec1 --> Page1[Page: Target platform]
    Sec2 --> Page2[Page: Instrument used]

    %% Question Layer
    Page1 --> Q1[Question: On which platform do you plan to publish your data?]
    Page2 --> Q2[Question: Which instrument do you plan to use to generate your data?]

    %% Attribute Layer
    Q1 -.-> Attr1[Attribute: .../publication/platform]
    Q2 -.-> Attr2[Attribute: .../instrument/pidinst]

    %% Option Layer
    Q1 --> OS1[OptionSet: Pigeon Target Platforms]
    OS1 --> Opt1[Option: OEP]
    OS1 --> Opt2[Option: Zenodo]
    OS1 --> Opt3[Option: Internal]

    %% Styling
    style Catalog fill:#f9f,stroke:#333,stroke-width:2px
    style Sec1 fill:#e1f5fe,stroke:#0277bd
    style Sec2 fill:#e1f5fe,stroke:#0277bd
    style OS1 fill:#fff9c4,stroke:#fbc02d