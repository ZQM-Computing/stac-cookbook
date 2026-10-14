# Security policy

## Supported version

Security fixes are applied to the `main` branch. This repository contains STAC catalog examples and validation patterns; it is not a hosted service.

## Reporting a vulnerability

Email **zqmcomputing@gmail.com** with the subject `stac-patterns security` if you find a vulnerability in the example code or workflow configuration. Please do not open a public issue for a sensitive report.

Include the affected file, the impact you observed, and reproduction steps when available.

## Publishing note

STAC catalogs are meant to be shared, which makes it easy to share too much: before publishing a catalog built from these patterns, check that item assets and link URLs don't expose internal hostnames, signed URLs, or credentials. An example here that leaks any of those is a bug worth reporting.
