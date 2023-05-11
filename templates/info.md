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