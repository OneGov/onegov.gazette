# Features

## Frontpage

- Commits
  - d592ba35d721b109713d697666cf5831890563a1
  - 4058bfdf830826df72609ea39529e18525c6c845
  - 86d5feeb2384a9388ce78e8cc29218cff638ebde
  - 6cd8ce350fab69ccf4530fd033f43f39ffa576d7
  - 7ba9fc9c0c1700e5f70f38024f1f2ac5c8edec3a
- What needs to be done
  - Make it dynamic/translated or/and use onegov.page
  - Remove/rename principal.show_archive (--> show_frontend?)
  - Use macros for showing notices

## Search

- Commits
  - e23d1ad0ae3fc666868fedb1b8521cd100dbb9c2
  - 44737089257339d0327ed70e82ec24bbfd585d93
  - 1a12bc5e96a20cc9013895d7fa0f4af8e22aaa23
  - db193dfc9319b9525d4e1aeef7f70dd9c8d114ac
  - f683149a5477483613e4d4e04a2640e3fb7c0d10
  - b6551be3d9541129baf02d113166e0a4c90c392c
  - be5c6d1b090648b249651f0adbe0992469ef9f6c
  - 7ba9fc9c0c1700e5f70f38024f1f2ac5c8edec3a
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
  - 5e01083846c977d1c77009ecea52fedef07f0c9e
- What needs to be done
  - Tests

## PDF View (Front-End)

- Commits
  - 96a9344684e1d7289d819998d23cc5017fa3aebd
  - 2e594df462bd8aed29f7230231d5f4b34e4fd9f1
- What needs to be done
  - Probably create the PDF as attachment
  - Sign it
  - Tests

## RSS

- Commits
  - 2fbca18a0ee0085faf97007db267ed84a856543c
- What needs to be done
  - Tests

## Subscriptions

- Commits
  - 985cfd3493c73f041429abb98f0ee7ecf51042d3
- What needs to be done
  - Tests
  - Optimize the CLI command (process-subscriptions), as this might get super slow with many subscriptions
  - Add a mechanism to cancel the subscription

## Press releases

- Commits
  - 43a934db4784de51da7100a9ccedbb214d02cbc0
  - 691900eabeccd88579cdf51fde01da4993725953
  - 7f65c0892aba6820bcc6da648a90429dfe8fb6dd
  - 6cd8ce350fab69ccf4530fd033f43f39ffa576d7
  - 2f22fe419bd49642664cabd24842e4c0ed70a322
- What needs to be done
  - Rework the whole thing?
  - Tests

## Backend Menu

- Commits
  - 1e46e2e728972a20eaca4fa8669c99f38f5898f6


## Editor Snippets

- Commits
  - 60e512b78dfac7aa398639f42a8843f0075504cf
  - d456bd4e58eb782d309222048f2ed879716a940f
- What needs to be done
  - Allow to define snippets and templates in the backend (per category, organization, etc.)
  - Tests


## SHAB Import

- Commits
    - 1540d1f8920528b9209e9ec4ec06b3d30da09368
    - e89f55ddbdc9ab1d02e7582a4a1311f12b534f0e
- What needs to be done
    - Rework importer and converters
    - Rework import view and/or add CLI interface
    - Tests

## Expiry Dates

- Commits
    - 7a817105c65df9566300b51d8932c72a6ed7ce77
- What needs to be done
    - Tests
