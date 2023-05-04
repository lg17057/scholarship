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