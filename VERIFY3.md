# Verification round 3 (v0.1.3)

An independent agent re-checked the features of the v0.1.3 work against their documentation, by probes, without the author's conclusions. Probes ran against `master` at `acd7fb4`.

## Fixed in this round (branch `fix-modal-generics`, tests/test_modal_generics.py)
- "Birds can fly." was stored as one unnamed bird with a modal. A modal over a generic (a bare plural, every, all) is now refused UNSUPPORTED_PREDICATE, as a modal in a rule.
- "Every bird can fly." was refused with the quantifier label. Now the same modal refusal.

## Open, recorded (not fixed)
- Control with a verb the grammar reads as a noun: "Lee tries to dance." reads "dance" as a noun, so no claim is stored (a reading choice limit; the grammar offers the noun reading).
- Conjoined infinitives: "Kim wants to sing and dance." stores one claim with the conjunction in its content, so "Does Kim want to sing?" is Unknown. Expected: Yes. Open.
- Robustness: a second `suppose` while one is open raises ValueError, and `drop()` with nothing open raises ValueError. These are API errors for the caller, documented as one level of supposition; they are not raised by any sentence.
- A supposition that contradicts a told fact ("Kim sings." then suppose "Kim does not sing.") answers Conflict. Undocumented; left as it is.
- Generated wording falls back to the template for "a dog" (`own(kim, a1)`, `a1 is a dog`): anonymous things have no name for the grammar to say. Documented in DECISIONS.md proofs item.
