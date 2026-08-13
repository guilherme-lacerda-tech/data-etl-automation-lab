    # Architecture

    ## Design Goal

    Demonstrate a safe ETL workflow using only synthetic operational data.

    ## Current Boundaries

    - Standard library first.
    - Synthetic input only.
    - Generated output ignored by Git.
    - No real systems, endpoints or credentials.

    ## Decisions

    - Separate ingestion, validation and output.
- Use manifests for auditability.
- Keep all sample data synthetic.

    ## Future Layers

    ```mermaid
    flowchart TB
        A["Mock inputs"] --> B["Collector / Loader"]
        B --> C["Domain validation"]
        C --> D["Rules / Processing"]
        D --> E["Persistence"]
        E --> F["API / Reporting"]
        F --> G["Automation workflows"]
    ```
