# ISL STEM Bridge

**An Indian Sign Language avatar for teaching science to Deaf students.**
Experiential Learning project, RV College of Engineering (Phase II) · Team 25, Byte Builders.

A web lesson in which a realistic 3D avatar performs Indian Sign Language (ISL) signs copied from
ISLRTC dictionary recordings, beside animated pictures, with captions and word cards in English and
Kannada. The first lesson is **photosynthesis**: 11 chapters, 67 animated steps and 41 word cards.

The avatar only performs real ISL recorded by ISLRTC signers. It never invents a sign or strings
dictionary signs together into sentences, and every sign is marked "Draft" until a qualified ISL
interpreter approves it.

## What is in this repository

| Folder or file | Contents |
| --- | --- |
| `ISL_STEM_Bridge_Survey.gs`, `Lets_Learn_Together_Survey.gs` | Google Forms surveys (Apps Script) |
| `School_Visit_Script.pdf` | Plan for the school visit |
| `isl_avatar/README.md` | Full project documentation; start here |
| `isl_avatar/player/` | The lesson page (open with a local web server) |
| `isl_avatar/avatar/avatar.glb` | The avatar with all its signs |
| `isl_avatar/tools/` | Tracking, quality checks, retargeting and report scripts |
| `isl_avatar/motion/` | Tracked body, hand and face data per sign |
| `isl_avatar/reports/` | Check results per sign |
| `isl_avatar/tests/` | Automated tests |

## Run the lesson

```bash
cd isl_avatar
python3 -m http.server 8811
```

Then open http://localhost:8811/player/

## Left out of this public copy

This is the public version of a private team repository. The following are not included:

- **ISLRTC dictionary videos** and every image or video that shows frames from them (the comparison
  previews and side-by-side check videos). The project has permission to use these recordings, not to
  republish them. Get them from ISLRTC.
- **School-visit photos**, the Phase-II presentation and the team walkthrough PDF, because they show
  students.
- **The Blender source of the avatar** (`avatar_source.blend`, 135 MB). The exported avatar
  (`avatar.glb`) is included and is what the lesson uses.

Some links in the documentation point to these files and will not open here.

## Credits

Signs: Indian Sign Language Research and Training Centre (ISLRTC). Avatar built with MPFB and
Blender. Tracking with MediaPipe. Lesson player with three.js.
