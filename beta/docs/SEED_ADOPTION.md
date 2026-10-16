# Voluntary seed adoption

`GET /adopt` is an anonymous, read-only entry point. It connects the existing
network, organism observatory, capsule, Docker installation and bounded hosting
protocol. `GET /adopt/manifest.json` describes the same paths for agents; it is
linked from `/llms.txt` and the capsule manifest. Reading it grants no authority.

## Three different experiences

- The browser demo uses fixed synthetic temperatures and two simple estimators.
  It is ephemeral, has no identity and executes neither the kernel nor full
  prospective genetic confirmation. Its share URL encodes only the estimator
  (`#demo-last` or `#demo-mean`); the recipient reruns the explicitly synthetic
  example. It never uploads input, calls an API or creates an account.
- `/organisms#seed-SAME` and `/organisms#seed-SAMM` link to the existing real
  observatory cards. These are current reports, not immutable snapshots. All
  status, missing-outcome and stale-report caveats remain. Identity or an accepted
  hosting request does not prove active computation, improved predictions or
  benefits to wellbeing.
- The local policy preparer emits only the existing hosting policy schema for
  one total birth, synthetic reference world and pump focus. Trial mode expires
  24 hours after preparation; persistent mode is explicitly chosen and revocable.
  Changing mode clears consent and output. Download is preparation, not local
  authorization or server publication. The Docker/identity/volume steps and
  `--allow-hosting` remain in the existing installation guide. No generated shell
  commands, credential handling, quota changes or auto-deployment were added.

Weather observers and the fixed signed-world hosting worker remain distinct.
The page links each to its actual guide. Adding systems, stations, resource
limits or permissions requires a separate reviewed change.

## Verification

From repository root, install `beta/requirements.lock` with hashes in a Python
3.12 virtual environment. Set:

```sh
export PYTHONPATH=beta:adaptive:twin:kernel:protocols:product_local:consumer_views
python -m unittest discover -s beta/tests -p test_seed_adoption.py -v
python -m unittest discover -s beta/tests -p test_public_network.py -v
python -m unittest discover -s beta/tests -p '*hosts.py' -v
node beta/tests/adoption_dom.cjs
node --check beta/genius_beta/static/adopt.js
node --check beta/genius_beta/static/organisms.js
```

The dependency-free DOM-unit test checks prediction/replay, navigation without
losing progress, clipboard failure, consent invalidation and JSON download. It
is not a browser layout or assistive-technology test.

`beta/tests/browser_adoption.cjs` is the Playwright desktop/mobile regression
check. Start the documented local Gunicorn service with a disposable data folder,
then set `GENIUS_TEST_URL` and `GENIUS_BROWSER_PATH` and run it with Node. It tests
consent, interrupted/repeated flows, download, horizontal overflow, stale reports
and the absence of write requests. Its only mocked API report is explicitly
synthetic test data; it never registers an organism or contacts an external host.

Deployment and production smoke testing are separate from preparing this change.
Do not invite people to a new route until the expected deployed commit and public
route have been verified.
