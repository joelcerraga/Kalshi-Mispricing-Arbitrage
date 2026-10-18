# Data and empirical reproduction

This public repository includes selected order-book observations, probability vectors, recorded notebook outputs and derived summary tables. The full raw API cache and complete processed historical quote panel remain in a separate private research snapshot.

The primary study used daily temperature series `KXHIGHNY`, `KXHIGHCHI` and `KXHIGHMIA` from 19 July to 16 October 2026. The noon observation rule, chronology and exclusions are recorded in `protocol/` and the paper.

`python scripts/reproduce_public.py` is the supported offline reproduction command. It runs the engine tests, verifies the frozen implementation and website package, and reruns the synthetic experiments without contacting Kalshi.

The eight empirical notebooks retain their actual recorded outputs. An exact empirical rerun requires the separately retained `data/raw/`, `data/processed/` and complete recorded output inputs. Verify the snapshot index and feature/prediction hashes in `protocol/model-freeze.json`. A newly downloaded response would be a new sample.

`scripts/reproduce.py` and the original collectors are retained for methodological transparency. Their full empirical pipeline requires the private source snapshot and is not the public reproduction command. Current terms and permissions must be checked before obtaining or redistributing a new sample. The client uses GET requests and submits no orders.
