```mermaid
 graph TD
    %% HMC Corporate Colour Palette Definitions
    classDef catalog fill:#002864,stroke:#001432,stroke-width:2.5px,color:#fff;
    classDef section fill:#0096d2,stroke:#002864,stroke-width:2px,color:#fff;
    classDef qset fill:#00aaa0,stroke:#002864,stroke-width:2px,color:#fff;
    classDef question fill:#e6f0f5,stroke:#002864,stroke-width:1.5px,color:#002864;
    classDef optionset fill:#fff,stroke:#00aaa0,stroke-width:2px,color:#002864;
    classDef attribute fill:#f4f7f9,stroke:#00aaa0,stroke-width:1px,stroke-dasharray: 3 3,color:#002864;

    %% Hierarchical Question Tree Structure
    subgraph Structure [Pigeon Catalog Structure]
        direction TB
        
        Cat["<b>Catalog: Pigeon: OEP Publication Catalog</b><br/><i>pigeon_oep</i>"]:::catalog
        
        %% Section 1
        Sec1["<b>Section: Publication Target</b><br/><i>publication_settings</i>"]:::section
        Qset1["<b>Questionset: Target Platform Settings</b><br/><i>target_platform_set</i>"]:::qset
        Q1["<b>Question: Target Repository</b><br/><i>Widget: select</i>"]:::question
        Opt1["<b>Optionset:</b><br/>publication_platforms"]:::optionset

        %% Section 2
        Sec2["<b>Section: Instrument Identification</b><br/><i>instruments</i>"]:::section
        Qset2["<b>Questionset: PIDinst Reference (is_collection=true)</b><br/><i>pidinst_set</i>"]:::qset
        Q2["<b>Question: Instrument PID (PIDinst)</b><br/><i>Widget: text</i>"]:::question

        %% Structural Links
        Cat --> Sec1
        Cat --> Sec2
        
        Sec1 --> Qset1
        Qset1 --> Q1
        Q1 --> Opt1
        
        Sec2 --> Qset2
        Qset2 --> Q2
    end

    %% Data Model Binding Zone
    subgraph Domain [Custom Domain Attribute Bindings]
        direction TB
        Attr1["<b>Attribute:</b> .../dataset/publication/platform"]:::attribute
        Attr2["<b>Attribute:</b> .../dataset/instrument/pidinst"]:::attribute
    end

    %% Element-to-Attribute mappings
    Q1 -.->|Saves response into| Attr1
    Q2 -.->|Saves response into| Attr2

    %% Structural Alignment Overrides
    style Structure fill:#f4f7f9,stroke:#002864,stroke-width:1px;
    style Domain fill:#ffffff,stroke:#00aaa0,stroke-width:1px;