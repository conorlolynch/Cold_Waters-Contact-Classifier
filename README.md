# Cold_Waters-Contact-Classifier
Program which classifies submerged contacts by their class of submarine using the broadband displayin the submarine simulator game Cold Waters

## Getting Started

Make sure to run the game in windowed mode at 1920 x 1080p resolution. 
Also make sure that hud scale is set to 1.5 so that numbers on screen can be read easier

After that just run the auto_contact_classifier.py file and watch as the algorithm classifies submerged contacts.

### Prerequisites

Following modules are required to run this program:

```
opencv-python == 4.3.0.36
PyAutoGUI == 0.9.50
numpy == 1.18.4
pywin32 == 228
scikit-image == 0.17.2
```

### Demonstration

![alt text](img/Cold-Waters-2020-09-09-14-11-53.gif)

### Additional Information

- This program was designed assuming CaptainX3's Playable Subs mod was also being used (more submarines in this mod). 
- For now the program only works with the Improved Virginia Class due the varying heights of the broadband display depending on the number of torperdo tubes each playable submarine has.
- For now only submerged contacts are properly classified and surface vessels are ignored.
- The program only works in custom games due to a bug with the playable subs mod which changes up the sequence of submarines and other vessels in the signature tab. This means this program will not work properly in campaign or quick missions.

### Desired Features
- Be able to run this program with all available submarines in the game.
- Classify both submerged and surface vessels properly
- Be able to run this in the campaign and quick missions without any issues.
