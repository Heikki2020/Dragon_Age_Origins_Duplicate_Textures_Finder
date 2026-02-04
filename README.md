# Dragon Age: Origins - Duplicate Textures Finder

&copy; Henry & Lukas 2025-2026

<https://www.nexusmods.com/dragonage/mods/6823>

### An app to compare textures when more than one high resolution texture packs are installed, making it easy to decide what to keep and what to delete.

It's been bothering me ever since I installed two high resolution texture packs for DAO, so I decided to write an app myself to remove duplicate textures.

Check out the screenshots first, as they will give you a quick overview of how to use the app.

- When it starts, the app will automatically scan **C:\Users\YOUR_USERNAME\Documents\BioWare\Dragon Age\packages\core\override**.
- It may take some seconds to finish the scan, if the folder is on an HDD or there are a lot of textures.
- And then, the app will list duplicate textures in the left column and show a short summary in the status bar.
- You can also click the **Browse** button to scan another folder.
- The app will only look for **DDS, TGA, PNG, JPG, JPEG** files (and ignore other formats), and group the files with the same file names.
- When you click a group, you can compare the textures in the right column by thumbnail, dimension, channel and file size.
- A tooltip will pop up displaying the full path, when you move the mouse on the thumbnail.
- The **Open** button will open the file in the default image viewer you set in Windows Settings, so you can view the texture at full size before you decide.
- For example, I use [oculante](https://github.com/woelper/oculante) to view DDS files and the button will start that app for me.
- The **Delete** button will send the file to the Recycle Bin, where you can restore the file easily or move it to another folder later.
- After you delete a file, the thumbnail will remain but become gray for reference.
