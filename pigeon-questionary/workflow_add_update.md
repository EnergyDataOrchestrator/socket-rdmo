```mermaid
graph TB
    %% HMC Corporate Color Palette Definitions
    classDef hmcFile fill:#00aaa0,stroke:#002864,stroke-width:2px,color:#fff;
    classDef hmcCmd fill:#0096d2,stroke:#002864,stroke-width:2px,font-family:monospace,color:#fff;
    classDef hmcServer fill:#002864,stroke:#001432,stroke-width:2px,color:#fff;
    classDef hmcWeb fill:#e6f0f5,stroke:#002864,stroke-width:1.5px,color:#002864;
    classDef hmcAlert fill:#d9381e,stroke:#002864,stroke-width:2px,color:#fff;

    %% Neutral Subgraph Styling
    style Prep fill:#f4f7f9,stroke:#002864,stroke-width:1px,stroke-dasharray: 3 3;
    style Execution fill:#f4f7f9,stroke:#002864,stroke-width:1px,stroke-dasharray: 3 3;
    style Verification fill:#f4f7f9,stroke:#002864,stroke-width:1px,stroke-dasharray: 3 3;

    %% 1. FIRST TOP ZONE
    subgraph Prep [1. File Preparation]
        direction LR
        A[attributes.xml]:::hmcFile
        B[options.xml]:::hmcFile
        C[catalog.xml]:::hmcFile
    end

    %% 2. MID INTERMEDIATE ZONE
    Server[/RDMO Server: /tmp/]:::hmcServer

    %% 3. EXECUTION ZONE
    subgraph Execution [2. Strict Terminal Execution Order]
        direction TB
        Step1[python manage.py import_domain /tmp/attributes.xml]:::hmcCmd
        Step2[python manage.py import_options /tmp/options.xml]:::hmcCmd
        Step3[python manage.py import_questions /tmp/catalog.xml]:::hmcCmd
    end

    %% 4. BOTTOM VERIFICATION ZONE
    subgraph Verification [3. Web Interface Verification]
        direction TB
        Web[Log into RDMO Admin Interface]:::hmcWeb
        V1[Manage -> Domain: Check project/dataset tree]:::hmcWeb
        V2[Manage -> Options: Check publication_platforms]:::hmcWeb
        V3[Manage -> Catalogs: Check Pigeon: OEP Catalog]:::hmcWeb
    end

    %% Explicit sequential linking to anchor layout top-to-bottom
    Prep -->|SCP / Transfer| Server
    Server --> Step1
    
    Step1 -->|Creates Domain Tree| Step2
    Step2 -->|Creates Optionsets| Step3
    
    Step3 -->|Success| Web
    Web --> V1 & V2 & V3

    %% Side-routed Error Handling path that won't disrupt the vertical stack
    Err[Delete conflicting element via Web UI]:::hmcAlert
    Step1 -.->|Constraint Error| Err
    Step2 -.->|Constraint Error| Err
    Step3 -.->|Constraint Error| Err
    Err -.->|Retry| Server
```
## on docker
```bash
python manage.py import ../rdmo-addons/pigeon_attributes.xml
```
## on host
```bash
psql -h localhost -p 5432 -U rdmo -d rdmo
```
```sql
SELECT id, uri, path, comment 
FROM domain_attribute 
WHERE uri LIKE 'https://kit.edu/terms/domain/project/dataset/%'
ORDER BY uri;
```
| id | uri | path | comment |
| --- | --- | --- | --- |
| 330 | [https://kit.edu/terms/domain/project/dataset/column](https://kit.edu/terms/domain/project/dataset/column) | project/dataset/column |  |
| 334 | [https://kit.edu/terms/domain/project/dataset/column/description](https://kit.edu/terms/domain/project/dataset/column/description) | project/dataset/column/description |  |
| 333 | [https://kit.edu/terms/domain/project/dataset/column/is_about](https://kit.edu/terms/domain/project/dataset/column/is_about) | project/dataset/column/is_about |  |
| 336 | [https://kit.edu/terms/domain/project/dataset/column/name](https://kit.edu/terms/domain/project/dataset/column/name) | project/dataset/column/name |  |
| 335 | [https://kit.edu/terms/domain/project/dataset/column/unit](https://kit.edu/terms/domain/project/dataset/column/unit) | project/dataset/column/unit |  |
| 331 | [https://kit.edu/terms/domain/project/dataset/instrument](https://kit.edu/terms/domain/project/dataset/instrument) | project/dataset/instrument |  |
| 337 | [https://kit.edu/terms/domain/project/dataset/instrument/pidinst](https://kit.edu/terms/domain/project/dataset/instrument/pidinst) | project/dataset/instrument/pidinst |  |
| 332 | [https://kit.edu/terms/domain/project/dataset/publication](https://kit.edu/terms/domain/project/dataset/publication) | project/dataset/publication |  |
| 338 | [https://kit.edu/terms/domain/project/dataset/publication/platform](https://kit.edu/terms/domain/project/dataset/publication/platform) | project/dataset/publication/platform |  |
 (9 rows)

## on docker
```bash
python manage.py import ../rdmo-addons/pigeon_options.xml
```
## on host
```bash
psql -h localhost -p 5432 -U rdmo -d rdmo
```
```sql
SELECT 
    os.uri AS optionset_uri, 
    o.uri AS option_uri
FROM options_optionset os
JOIN options_optionsetoption oso ON os.id = oso.optionset_id
JOIN options_option o ON oso.option_id = o.id
WHERE os.uri = 'https://kit.edu/terms/options/publication_platforms';
```
| optionset_uri                                       | option_uri                                         |
|-----------------------------------------------------|----------------------------------------------------|
| https://kit.edu/terms/options/publication_platforms | https://kit.edu/terms/options/platform_oep         |
| https://kit.edu/terms/options/publication_platforms | https://kit.edu/terms/options/platform_zenodo_test |
| https://kit.edu/terms/options/publication_platforms | https://kit.edu/terms/options/platform_internal    |

(3 rows)

## on host (script is on docker)
```bash
docker exec -w /vol/rdmo-app -i rdc-rdmo python manage.py shell -c "exec(open('/tmp/delete_kit.py').read())"
```

## on host (script is also on host)
```bash
docker exec -w /vol/rdmo-app -i rdc-rdmo python manage.py shell << delete_kit.py
```