# Features

## Fixes

- Commits
  - 0bb81ad1d8a3985109a3dbf48c20de99c2508580
  - aa0b3a9b85485324b24fd88836fdb5c1f6a053fa
  - cd19a41b8eb2f51483364ce1a201631983889f2b

## Import & Exports: Issues, Organizations, Categories

- Commits

  - 4f2eb2da611b26abab845f1ecaf584b72e149d20
  - b3526237a99f92afc9d656b52fb5558c6a02eb30
  - b3526237a99f92afc9d656b52fb5558c6a02eb30

- What needs to be done

  - Write tests

  - Import/Export the external ID of organizations

## Frontpage

- Commits
  - d592ba35d721b109713d697666cf5831890563a1
- What needs to be done
  - Make it dynamic/translated or/and use onegov.page
  - Remove/rename principal.show_archive (--> show_frontend?)

## Search

Suche

- Commits
  - e23d1ad0ae3fc666868fedb1b8521cd100dbb9c2
  - 44737089257339d0327ed70e82ec24bbfd585d93
  - 1a12bc5e96a20cc9013895d7fa0f4af8e22aaa23
  - db193dfc9319b9525d4e1aeef7f70dd9c8d114ac

- What needs to be done
  - Tests
  - Honour principal.show_archive/frontend (possibly raise NotFound in path.py or redirect if disabled)

## PDF Export of Notices (Back-End) 

- Commits
  - 414fa8a634f48147f156227de2f6e49bf276263a
  - d49514d7afaf84e66bcc065eaf405085bf94579d
- What needs to be done
  - Tests
  - Improve Performance

## PDF Preview (Back-End)

- Commits
  - 930be3b6db78c8d5beec185fdbd2de150c09b308
  - 21d392606d7368d40d4d84e13614b803834de67e
- What needs to be done
  - Tests

## Subscriptions

- Commits
  - 985cfd3493c73f041429abb98f0ee7ecf51042d3
- What needs to be done
  - Tests
  - Optimize the CLI command (process-subscriptions), as this might get super slow with many subscriptions
  - Add a mechanism to cancel the subscription