PyFighter

A Fighting Game Engine built in PyGame

Created by Sam Von Ehren

This engine is licensed under the Creative Commons License 
http://creativecommons.org/licenses/by/3.0/

--------------------------------------------------------------

INTRODUCTION

PyFighter is a Fighting Game engine developed in Python using the PyGame library.
A majority of the functionality is precoded to allow game designers to create 
fighting games by creating a few text files and sprite sheets. Any more substantial changes
would require a programmer, but the engine attempts to be readable and easy to modify.

CREATING A GAME

Creating a game with PyFighter is fairly simple, but can be an involved process due to the complexity
of fighting games. PyFighter uses text files to create characters using sprite sheets. You will
need sprite sheets to use PyFighter, but everything else is handled by text files.

To create a game, put your character spritesheets inside the "data" directory, along with the image you'll
use for your character select. First you'll have to create a file for the character select called "characterselect.txt". All of the text files you'll be making in thisengine have to properly formatted or the engine will crash. The format looks like this:

filename
Bounding Box for cursor movement (in the format of x,y,width,height)
player1 cursor (same format)
player2 cursor

then for each character in your game, you put what coordinate they will be selected at, and the datafile for that character
followed by an &

this is probably a little confusing so the following is the example file included sample file:

character_select.jpg
200,100,200,150
200,100,100,150
300,100,100,150
200,100,100,150
datafile.txt
300,100,100,150
ken.txt
&

I'll break this down line by line: "character_select.jpg" is the picture that will form the character select
"200,100,200,150" means I'm making a bounding box on that picture that starts at 200 pixels from the left and 100 pixels
from the top that has a width of 200 pixels and a height of 150 pixels. The next line ("200,100,100,150") is player1's cursor. As you my have guessed by comparing those coordinates to the bounding box, the cursor sits on the left half of the box (x and y are the same, but width is cut in half). when player 1 hits left or right, the cursor will be moved by its width, as long as it stays withint he bounding box. In this case player 1 hitting left, up, or down will result in no action. The next coordinate is the same thing, but for player2, and it is appropriately on the right half of the bounding box. 

The next lines are a coordinate (though I included the width and height due to lazy programming), followed immediately by a datafile. If a cursor is in that space when the player hits confirm, the character defined in that file will be loaded for that player. In this case player 1 is on "datafile.txt' (which is ryu) and player2 starts on "ken.txt". After you are done defining these, put a simple ampersand to signify the end of the file.

So now that's out of the way. Now we can move onto the actual character datafiles. The setup is fairly open, but if you aren't careful you can get odd effects and crashes. If you open "datafile.txt" you can follow along with my descriptions

The first line of the character file is the spritesheet. After that there are a few things you must define. The form for each definition involves writing a key, and then the coordinates that go along with it. in datafile.txt, the first key we see is "walkingForward", which defines the animation for forward movement. Each line of coordinates represents one frame of the animation. In this case there are 6 frames, each one defined as above by x,y,width,height (with x,y defining the top left corner of the rectangle). After the 6 frames, there is an &, which tells PyFighter that you are done defining the walk forward animation. The following keys are stand alone and need to be defined individually:

walkingForward
walkingBackward
knockDown
hit
thrown

After these we have the State Keys:

jumping
standing
crouching

With each of these states you must define the actions the players can do in these states, but the actions only break down into two groups at this point: blocking and attacks (airblocking for jumps is not implemented yet, incidentally). So we'll
start with standing, because it actually contains more sub keys than the other states.

If you scroll down to the line that says "standing" in datafile.txt, you'll see there are a bunch of coordinates afterwards. This is the neutral animation for this state. In this case it's 5 frames long and will loop indefinitely while the player is in a standing state. Also notice again that the list of frames is ended with an &. After the first &, you can see "normalMove" This key tells PyGame that you are defining a move. A normalMove definition looks like this:

normalMove
input
type
damage,hitstun,knockback,knockdown
blockType
animationFrames
&
hitBoxes
&
velocities
&
@

I'll break this down again twice to show off different types of moves. In this cause the move is a throw, and since throw is mapped to one button in this game, "THROW" is the input sequence for this move. After that we see "melee" which means it's a physical attack and not a projectile. After that is the numbers behind the move, namely damage, hitstun,knockback, and knockdown. The first three are self-explanatory, but the last one can be confusing. If the last number is 0, the move does not knockBack. If it's any other number, then the move will knockdown. Blocktype is the final parameter. It defines lows or highs. In this case the move is unblockable, so we write "throw". After that we have a setup similar to before. You define the frames for the animation, then put an &. After that, you define the hitbox for each frame. These numbers are relative to the character. The first two frames have no hitbox, and then the next one (80,0,30,100) is 80 pixels from the top left point of the character's hitbox, 30 pixels wide and 100 pixels tall. The throw is actually a weird case here because the hitboxes are how the other character's movement is determined, which is why there are so many frames. 

After that &, we come to velocity. The text here is just an x and a y which is your change in x and change in y. In this case it's (0,0) for each frame because we aren't moving. If we were moving in either direction, these would be filled in. After you finish the & for the velocities, you put in an @ sign to show the move is defined. Let's look at a standard fireball so we can compare the differences. Scroll down to the normalMove where you see "DOWN,DOWNTOWARD,TOWARD,JAB". Fighting game afficionados will realize that this is a basic fireball move. Notice that this is still being defined in a normal move. You can write in any inputs that are valid here and they should work (if they don't, let me know). Things get different afterwards: it's labeled as a projectile. At the moment, PyFigher has a bulit in projectile animation that it uses, but in the future the projectile will be defined here. If you look through the move things are similar, though there are no hitboxes because the projectile has its own, and there is no movement. Everything else functions the same.

The last key I need to cover is the "block" key, The block key functions like the normal keys above. You type the key, type in the coordinate, then put an &.

And that's it. Have fun. 

Known Issues
--------------------------------------


- Generally weak performance
- Player2 Hitboxes are functional but not as good as player1's
- Players can't confirm their characters individually
- Throw animation isn't there yet
- air blocking
- No sound effects or Music
- The entire frame of a character is hitable, meaning the space above a character's shoulder can be hit in the air
- Projectiles are not unique for each character