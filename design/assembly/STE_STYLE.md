# BEN Engine — Simplified Technical English (ASD-STE100) writing rules

One page. Every assembly, maintenance and commissioning document for BEN Engine obeys these rules.
Issue B, 2026-11-08 (generation-2 vocabulary). Source: ASD-STE100 Issue 8 writing rules and dictionary, applied to BEN Engine.

## Sentences

1. Write one instruction in one sentence. Do not put two instructions in one sentence.
2. Keep an instruction to 20 words or fewer. Keep a descriptive sentence to 25 words or fewer.
3. Use the imperative for instructions: "Torque the bolt to 85 N·m." Not: "The bolt should be torqued."
4. Use the active voice. Say who does the action: "The welder welds the frame." Not: "The frame is welded."
5. Keep the articles: "the bolt", "a label", "the rack". Do not drop them to save words.
6. Use the present tense for descriptions. Use "will" only for a future result that the reader must expect.
7. Start a step with the verb. Put the condition first only when the reader must know it before the action: "If the light is on, do not open the door."
8. One topic per paragraph. Start a new paragraph for a new topic. Keep a paragraph to six sentences.

## Words

9. Use only approved words, and use each word with one meaning. Approved verbs for BEN documents:
   **install, remove, attach, connect, disconnect, tighten, torque, loosen, fit, put, lift, lower, move, measure, mark, cut, drill, weld, seal, apply, clean, examine, test, record, read, press, open, close, start, stop, set, adjust, make sure, obey, hold, keep, wear, use**.
10. Do not use these words. Use the approved word instead:
    - ensure → **make sure**
    - utilize / employ → **use**
    - follow (a procedure) → **obey**; follow (a cable) → **trace**
    - verify → **make sure** or **examine** or **test**
    - secure (a bolt) → **tighten** or **torque**; secure (a load) → **attach**
    - locate → **find**; position (verb) → **put**
    - perform / carry out / conduct → use the action verb itself ("test", "measure")
    - approximately → **about**; prior to → **before**; subsequent to → **after**; in order to → **to**
    - check (as a verb) → **examine** or **make sure**. "Check:" is permitted as a heading only.
    `design/assembly/gen_assembly.py` reads this list and stops with an error when a generated document uses one of these words or has a step sentence over 20 words (rule 2). `scripts/audit.py` A10 repeats the check on the written files.
11. Use the same word for the same thing in every document. Rack, not cabinet or enclosure, for an IT rack (the BEN 5 outdoor housing is "the cabinet"). Cooling unit, not CRAC or AC, for an in-row unit; cabinet air conditioner for the BEN 5 unit. Pod (BEN Pod), not node, sensor board or sensor module. BEN Controller panel, not gateway or controller cabinet, for the controls panel; PLC for the PLCnext (Pro) and RevPi for the Lite controller; edge computer for the OnLogic computer that runs `ben_engine`. Never write node or gateway.
12. Technical names from the drawings and the protocol are permitted as written, even when they are not in the dictionary: tags (R1, CU2, PNL-M), channel names (T_in_r1_0.4), item codes (PWR-100), standards (NEC 110.26), and part names from a manufacturer.
13. Write numbers as digits with the unit: 85 N·m, 914 mm, 30 minutes. Write a tolerance as +/-10 % or +0/-6 mm. Do not write "approximately 1 m".
14. Do not use slang, idioms, or words with more than one meaning in the same sentence.

## Warnings, cautions and notes

15. Put a WARNING or a CAUTION before the step it applies to, never after.
16. WARNING: a risk of injury or death to a person. CAUTION: a risk of damage to equipment. NOTE: information only, never an instruction.
17. A warning has three parts in this order: the danger, what to do, what happens if you do not. Example: "Refrigerant can freeze skin. Wear gloves and eye protection. Contact causes burns."
18. Do not put an instruction in a NOTE. Do not put a warning in a step.
19. HOLD POINT and WITNESS POINT are written in capitals at the start of the warning that introduces them. A HOLD POINT names the qualified person who may continue the work.

## Structure of a task

20. Each task has these parts in this order: title, personnel, time, tools, parts (with item codes), warnings and cautions for the whole task, numbered steps, and "Check:" lines.
21. Each "Check:" line has: the CTQ or CTP reference in brackets, the measurement or observation, the acceptance value with its tolerance, and the QC form that records it.
22. A step may contain a short list of items (positions, cutouts). The list is indented under the step. The numbering continues after the list.
23. Positions use the drawing coordinates: x from the door-end liner, y from the rack-wall liner, z from the finished floor, in millimetres.

## Checking a document

24. Read each sentence and count the words. Split any instruction with more than 20 words.
25. Search for the words in rule 10. Replace every one.
26. Read each warning. Make sure it is before its step and has the three parts of rule 17.
27. Give the document to a person who has not built the unit. Ask the person to read one task and to say what to do. If the person asks a question, the text is not clear enough. Change the text.
