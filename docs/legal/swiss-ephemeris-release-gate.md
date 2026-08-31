# Swiss Ephemeris release gate

Lá Lành uses the official Swiss Ephemeris C source directly. The upstream license requires a choice before software distribution or activation of a public service:

1. release the complete combined work under AGPL-3.0 or a compatible license and satisfy its network-source obligations; or
2. purchase and sign the Swiss Ephemeris Professional License.

## Gate

Production/public deployment is **blocked** until the product owner records one of those two choices and legal review confirms it. Preview builds must remain private and access controlled. The vendored copyright and license notices must remain intact in every build and source distribution.

Evidence required to open the gate:

- chosen license model and approval owner;
- signed professional agreement or AGPL release checklist;
- release artifact retaining upstream notices;
- deployment configuration explicitly acknowledging the license choice.
