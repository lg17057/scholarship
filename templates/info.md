I have started work with the table and sorting it, and selecting a date and it taking the user to the url of that date
The date format is now - dd-mm H-M instead of YY-MM-DD H-M


Fixed an issue where the submitted_under was not represented in the table and so the items were displaced by 1 

date selection now working

created check for if the user selects a date and there is no data for that date
note that the date selection still works if there is an hour and minute recorded

---------------

work on the new log has been created 
custom message for rental logs page made

creating login and signup button to prevent KeyErrors and other associated errors
KeyError occurs with session when there is no user logged in and therefore there is no user_id that is put into submitted_under when creating a new log 

first check for whether user is logged in is functional
issues with the key not being set encountered 

login button and signin button made and now being added to all pages
check added so that if the user is not logged in, they cannot access the pages

created class login_verification
not working yet

working on login page that models login page on bridge

custom changeable div now added so that i dont need to redirect a user to a new html/link/url

--- for sunday
start work on moving the items in the first div
the back button for div 2 is now working having changed the js

login page div changer no longer working

login page div changer now working
This was a result of the login-div encompassing the other student and staff login divs, which means that when the back button was pressed, no content would be shown

sign in with google page button now working
signing in with google does not work yet but the button is there
fixed a couple of other issues
---
9/05
created QR Code Return branch
Started work on trying to scan a device qr code to rent a device and to return it
css for new modal moved to external file

ask mrs gamil if she wants a qr code or a barcode,,,, and if she wants a scanner or a device camera
used pip install python-barcode

Made barcodes have a 12 digit number underneath, in format 'device_id''random_8-character-string'

-----
Client meeting with mrs gamil
Chromebooks, ipads and laptops can be rented but laptops less often
Want barcodes not qr codes
Make the bottom of the barcode say 'Device Type' : 'Device_id
----

Researching the scanner;

-How to get data from scanner into excel
-How to get data from scanner into python
-How to get data from scanner into database
-Can it extrapolate data from a student id; can a database of student IDs be foud or made, which then provides student data from scanning
----
Should it be recorded how many times a device has been rented/last time rented/last student to rent
Create a students table in database that records all students who have rented a device, and the number of times, and the last time they rented??
----
new page for each barcode created based off of the device id that the barcode is associated with
barcodes now have the deivce type and device id underneath the barcode itself
----
ask Mrs Gamil how many digits each device ID is 
if so, limit the input for a new device creation field

fix circulations table issues
^
fixed

make it so that when the user presses the enter button when submit button is not visible, the popup will not appear

table css changed

Ask Mrs Gamil if a device 'ipad' and device 'chromebook' can have the same ID. And are the device ID's generated a certain way? is there a certain format.

-----
12/05 

student_data table in logs.db made
new issues for research and development created
----

format in excel
or as pdf 
-----
should create a custom message page button based off of what the issue encountered was

also figure out how device modifier will work and what it will do

make it so the admin has to re-enter password before acessing admin page?

style circulations page

change device retal logs device id based links - done
do the same for the sign off device id system -  done

"now accomodates for devices of different types having the same id"

create device id input that allows user to type in a device id to see that devices confirmations on 
^ for sign off page
^ for rental logs too
^ could be a popup to select device ID and device type and then go to the link

change custom main title sign off message so that it displays the device type AND ID
-------------

program now upadtes devices, device_logs and student_data.
Fix issue where num_rentals is null and unable to be changed
--this issue has been fixed by setting the number of rentals to 0 when the student data is created 


create cascading device dropdown menus that work based off of suffix and prefix? or wait until scanning system works
or maybe in case scanning system never works do it anyways



for download logs page
have first div that has buttons to choose what type of data to download - eg choose between device data, student data, homeroom data, logs data or user data
User Data;
- Download the following?;
- - List of admin usernames, accompanied by the identifier number - randomly generate this when user created maybe?

Student Data;
- Download the following?;
- - Student Name
- - Student ID?
- - Homeroom
- - Number of Rentals
- - Date of last rental
- - Device_id
- - Device Type
- - Outstanding/Current Rental 
- - Notes


Homeroom Data;
- Download the following?;
- - Homeroom
- - Teacher
- - Year Level


Rental Logs Data;

- Choose by device type
- Choose by device ID
- Choose by device type and ID
- Choose by date
- Choose from date 1 to date 2
- Download all data?
-----------
wokring on the 4 different divs for these data types and the back buttons

barcode not working? enter manually option
-----------
CSS fixed on circulations page
extra notes column added to circulations and device logs page as a bug fix
admin page styling fixed fire side/top nav and buttons on the page 
sign up page css fixed as a result of user feedback
-
trying to fix issue where i cant see the confirm selection button for device id and type picker on rental logs page 
fixed this issue
--- 

working on the system that the librarika website uses that displays overdues and checkouts (rentals)
done

-----

couldhave two separate links for renting and returning a device- think of implications
makes it take more time
possibly less friendly for usiers unfamiliar with database
make help continue with theme of whole website 
expand on this


make issues in github corresponding to what ive done - done
make it so that no user is required to be logged in to rent/return? - done
make it so everything else requires user logged in/admin logged in - done
remove sign up page access except for an admin login confirmation? - done


login to access page feature done
message = "Please login as an admin to create new admin account"


-----------

Now working on rental/return manual functionality
Figoure out how to differentiate the two forms being submitted


For renting this means;

Logging all data to device logs, set period returned and teacher signoff to "Not Returned" and "Unconfirmed"
Creating or modifying student data; outstanding_rental = yes, num_rentals, last_rental, device_id, device_type 
Modifying device data; num_rentals and in_circulation


For Returning this means

Modifying rental data; period returned, 
Modifying student data; outstanding_rental = no, 
Modifying device data; num_rentals and in_circulation
--------------

This feature is done

user radio buttons for download buttons
````````````````````````````````````````````````````````````````````````````````````````````````````````````

check if devices exists isnt working
num rental isnt going up when renting

`````````````````

check for whether or not the device type and id combination exists is now working
as well as route check for if device exists is now working



``````````````````````````````````````
4-06

moved rent/return fucntionality to index page
fixed several different container not showing issues
count succesfully added to index page using different method (len(rows))
checkouts table working again
overdues table working agani

make all of these errors in the github
make a thing at the bottom of the page showing how many overdue items there are 


device type and id valid for rental page
added to overdues
removed one of the rental logs routes

-removed in_circulation = no from rental logs valid device types and ids query so that only the devices that dont exist are not allowed to be    submitted instead of ones that arent in circulation

fixed issue when submitting the device type and id and the device id is NONE. name="device_id" had to be bet into device Id form

make comments on issues closed recently

name for date picker on download page had not been set - fixes None issue when downloading
``````````````````````````````````````````````````````````
DOWNLOAD PAGE
making mockup for the download page

sliding bars and confirm button js/css working

fixed issue of confirm button being wrong place when bar 1 is first opened

fixed issue where date 1 < date 2 message would show when date 1 was selected but 2 wasnt
made it so that date 1 < date 2 message wouldnt show when date 1 is not selected

slide in animation for date 2 working, slide out not
