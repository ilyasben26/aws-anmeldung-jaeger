![logo_aj](https://github.com/ilyasben26/aws-anmeldung-jaeger/assets/73348981/611c8cd8-b3ce-4e4d-bbee-ea28b263fde1)

Visit here: http://anmeldung-jaeger.com

# 1. Introduction
When moving in to another residence in Germany, the Anmeldung is know to be quite the hassle, especially when the appointments are few and highly sought after. But what if you could immediately get notified as soon as an appointment is available? That is exactly what this small project of mine aims to accomplish. 

With the help of AWS's serverless services, the goal is to create a solution that continuously checks the respective portals for most major German cities, in search of those juicy free appointments and quickly notifies the users so that they can go ahead and secure their spot. 

Ideally, I would build this solution using only severless services in AWS and without exceeding the AWS free tier; costs must be kept to a minimum.

I will be using the following services:
- *AWS Lambda*: for crawling the portals and publishing the results to S3 and notifying users via SNS
- *Amazon DynamoDB*: to act as a cache for persisting variables between Lambda functions
- *Amazon SNS*: to notify users
- *Amazon S3*: for creating a website which will display the available appointments as well as storing the results of the Lambda functions
- *Amazon Route 53*: to register and configure the domain
- *AWS IAM*: to configure the necessary roles and permissions

# 2. The Architecture
![Anmeldung (4)](https://github.com/ilyasben26/aws-anmeldung-jaeger/assets/73348981/0ce6dce6-ea15-4c92-bc4a-0684b548157e)


# 3. Development
## 1. Reverse Engineering the Portal 
In previous iterations of this project *link GitHub*, I wrote a python script that would use a selenium headless browser to crawl the website. This previous solution proved to be too clunky and with too much overhead, so for this iteration, I will try to only use GET requests to get the data that is needed from the website. This is also better since it will make it way faster and hence cost less in terms of resources.

The first step is to understand how the portal works, for this I will be going through a normal workflow to book an appointment and analyse each request made via the browser using BurpSuite, that way I can reproduce the same steps programmatically inside the Lambda function using Python.

I will first create the function for the Bremen portal.
Bremen uses a unified portal for booking all kinds of appointments, the first page looks like as follows:

![Pasted image 20231222151043](https://github.com/ilyasben26/aws-anmeldung-jaeger/assets/73348981/89ba5764-d556-4138-bb31-3695cd146ff4)

As we can see the initial GET request to the portal is made via the url `https://termin.bremen.de/termine/`, from this request, we learn the following:
- A session cookie called `tvo_session` is set to establish a session. The session lasts for 24 minutes as show below

After choosing one of the options from the list, a GET request is made to the following url `https://termin.bremen.de/termine/select2?md=5`:

![Pasted image 20231222151512](https://github.com/ilyasben26/aws-anmeldung-jaeger/assets/73348981/49bb24bf-1406-4931-a888-02d692386572)

Upon further testing, the following is apparent:
- `select2` signifies that we are on the second step of the booking process
- the `md` parameter here is referring which option was chosen, in this case it was BürgerServiceCenter-Mitte, which if we look at the first screenshot does coincide with the sixth position (by indexing at 0), hence why `md=5` points to it.

Let's now try and select which kind of appointments I want to book, I will focus solely on Anmeldung appointments. After clicking a bunch of buttons, I get this curious request being made:
```HTTP
GET /termine/location?mdt=701&select_cnc=1&cnc-8580=0&cnc-8582=0&cnc-8583=0&cnc-8587=0
&cnc-8597=0&cnc-8579=0&cnc-8596=0&cnc-8599=0&cnc-8600=0&cnc-8797=1&cnc-8790=1
&cnc-8588=0&cnc-8591=1&cnc-8798=0&cnc-8573=0&cnc-8844=0&cnc-8867=0&cnc-8789=0
&cnc-8575=0&cnc-8578=0&cnc-8590=0 HTTP/1.1
```
After some testing, I came to the following conclusions:
- `mdt` is an id for which location the appointment is booked
- `select_cnc` must always be set to 1.
- `cnc-$$$$` are used for tracking which services the user wants to book and how many of them, for Anmeldung services, it is either set to 1 or 0

After this request, we get a summary page of all the services we want to book:

![Pasted image 20231222153212](https://github.com/ilyasben26/aws-anmeldung-jaeger/assets/73348981/f6808494-f45e-40cb-95de-783ff5bb2b50)

After clicking on that `auswählen` button, the following happens:
- A post request is made:
```HTTP
POST /termine/location?mdt=701&select_cnc=1&cnc-8580=0&cnc-8582=0&cnc-8583=0
&cnc-8587=0&cnc-8597=0&cnc-8579=0&cnc-8596=0&cnc-8599=0&cnc-8600=0&cnc-8797=1
&cnc-8790=1&cnc-8588=0&cnc-8591=1&cnc-8798=0&cnc-8573=0&cnc-8844=0&cnc-8867=0
&cnc-8789=0&cnc-8575=0&cnc-8578=0&cnc-8590=0 HTTP/1.1
Host: termin.bremen.de
Cookie: tvo_session=3uk7kduf8iuei2d4cikb17ogll
...
...
...

loc=680&gps_lat=999&gps_long=999&select_location=B%C3%BCrgerServiceCenter-Mitte+ausw%C3%A4hlen
```
- Then a GET request:
``` HTTP
GET /termine/suggest HTTP/1.1
Host: termin.bremen.de
Cookie: tvo_session=3uk7kduf8iuei2d4cikb17ogll
User-Agent: Mozilla/5.0 (X11; Linux aarch64; rv:109.0) Gecko/20100101 Firefox/115.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate, br
Referer: https://termin.bremen.de/termine/location?mdt=701&select_cnc=1&cnc-8580=0&cnc-8582=0&cnc-8583=0
&cnc-8587=0&cnc-8597=0&cnc-8579=0&cnc-8596=0&cnc-8599=0&cnc-8600=0&cnc-8797=1&cnc-8790=1&cnc-8588=0&cnc-8591=1
&cnc-8798=0&cnc-8573=0&cnc-8844=0&cnc-8867=0&cnc-8789=0&cnc-8575=0&cnc-8578=0&cnc-8590=0
Dnt: 1
Upgrade-Insecure-Requests: 1
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: same-origin
Sec-Fetch-User: ?1
Te: trailers
Connection: close
```

After analysing these two requests and some testing, I came to the following conclusions:
- The browser asked to know my location before sending the POST request, this has something to do with `gpc_lat` and `gps_long` parameters, it seems like this is being used to suggest which location is closest to the user and has no importance for the workflow. If the user choose to block the location request, these two parameters are set to 999
- `loc` and `select_location` are used for the location. `loc` is an ID and `select_location` always has the name of the location plus *auswählen*

The last GET request to `/termine/suggest` is used to fetch the results of the previous POST request by showing the user which appointments are available, in case now appointment is available, the following is shown:

![Pasted image 20231222154717](https://github.com/ilyasben26/aws-anmeldung-jaeger/assets/73348981/958c889a-227e-4d0e-852c-ba277f764c7a)

To summarise the following is needed to check if appointments are available:
1. Make a GET request to the portal to get a session cookie (`/termine`)
3. Make a GET request to the specific page for a location (`/termine/select2?md=$id`)
4. Make a GET request in which we specify the request service using the url parameters (`/termine/location?mdt=$id&select_cnc=1&cnc-8580=0 ...`)
5. Make a POST request in which we specify the request service as using url parameters as well as some parameters in the request body (`/termine/location?mdt=$id&select_cnc=1&cnc-8580=0 ...`) 
6. Make a final GET request to get the results (`/termine/suggest`)

Armed with this knowledge of how the portal works, I can now begin automatising the appointment checking process.

## 2. Lambda function
Now, to automate the process, I will be using Python along with the `requests` library to make the needed GET and POST requests. 

To organise the Lambda functions, I will need to make a Lambda function for each City since the portals differ from city to city and as such, the process and code for checking the portals differs as well.

I called lambda function `lambda-anmeldung-jaeger-checkBremen`, it does the following in order:
1. Check all the locations in the Bremen portal using HTTPs requests
2. Write the results as a JSON object to an S3 bucket called `anmeldung-jaeger.com` as `data.json`
3. If any of location has available appointments, it publishes a message to the SNS topic for Bremen
	- When publishing messages, it uses a message throttling system which only allows it to send on message every 20 minutes, this system uses a DynamoDB entry as a way to track when the last message was sent and act accordingly

Here is a small snippet of the lambda function's event handler which summarises the previously described behaviour:
```python
def lambda_handler(event, context):
  
    bremen_list = data["Bremen"]

	# checking the portal for each location
    results = scrapeFunc.check_bremen(bremen_list)
    
    # writing the results to S3
    modify_s3_data_object(results)
     
    # sending a message if any of the locations have available appointments
    if any(item["status"] == "available" for item in results):
        
        print("DEBUG: Available appointments!")
        
        # Calculate the current time
        current_time = datetime.now()
        print(f"DEBUG: current_time={current_time}")
        
        if SEND_MESSAGE:
            # Check the DyanamoDB table for the last message timestamp
            last_message_time = get_last_message_time()

            # If more than the specified minutes have passed, publish a message to SNS

            if last_message_time is None or (current_time - last_message_time) >= timedelta(minutes=MESSAGE_THROTTLE_MINUTES):
                message = format_message(results) 
           
                send_sns_message(message)
                update_last_message_time(current_time)
            else: 
                print("DEBUG: SNS message throttled")
        else:
            print("DEBUG: SEND_MESSAGE is set to False")
        
    
    return results
```

To make this Lambda function run every 5 minutes, I used the *Amazon EventBridge Scheduler*.

I also had to give it the appropriate permissions via a role where I used *the principle of least privilege* to only grant it the bare minimum permissions that it needs:
- `logs:CreateLogStream` and `logs:PutLogEvents` to allow the function to be logged in *CloudWatch Logs*.
- `s3:PutObject` on `arn:aws:s3:::anmeldung-jaeger.com/data.json` to allow the function to modify the object.
- `dynamodb:GetItem` and `dynamoDB:PutItem` on the cache DynamoDB table to allow the function to read and write the cache table.
- `sns:Publish` on the SNS topic for Bremen to allow the function to publish messages.

To see the function's complete code check the GitHub repo link: *insert link*

## 3. S3 Website
To make the results accessible to end-users, there are two ways, the user can either simply visit a website and see an overview of all the available appointments or the user can register their email to the SNS topic and receive an email as soon as there is a free appointment. The latter option is still a work-in-progress and will be released soon, for now, I am the only one getting notifications sent to my email via the SNS topic.

To create the website, I will be using S3 static website hosting to host it. The website is quite simply at the moment, it simply consists of two files:
- `data.json`: the file is being continuously updated by the Lambda function every time with the latest available appointments, the file looks like this:
```json
[
  {
    "location": "BürgerServiceCenter-Nord",
    "status": "available",
    "datetime": "25/12/2023 13:39:56",
    "days": [
      "Donnerstag, 18.04.2024",
      "Freitag, 19.04.2024"
    ]
  },
  {
    "location": "BürgerServiceCenter-Mitte",
    "status": "not available",
    "datetime": "25/12/2023 13:39:59",
    "days": []
  },
  {
    "location": "BürgerServiceCenter-Stresemannstraße",
    "status": "available",
    "datetime": "25/12/2023 13:40:01",
    "days": [
      "Donnerstag, 18.04.2024",
      "Freitag, 19.04.2024"
    ]
  }
]
```
- `index.html`: the main page of the website, it uses client-side JavaScript to fetch the `data.json` file from the same origin (hence no CORS errors are raised) and formats the results in a more human-readable fashion:
  
![Screenshot 2023-12-26 at 09 03 35](https://github.com/ilyasben26/aws-anmeldung-jaeger/assets/73348981/5e7fd77a-e5e7-4be5-b37a-e613ff19ffd3)

## 4. Route 53
To make this whole operation more trustworthy and also give the German authorities a way to contact me in case the website unintentionally broke some laws, I bough the domain name `anmeldung-jaeger.com` for the meagre sum of $13 per year using Route 53.
I then added an `A Record` pointing to the S3 bucket, you can now visit `http://anmeldung-jaeger.com` and see my website.
# 4. Conclusion
Through this small project, I had the chance to apply some of the theoretical knowledge I acquired from studying for the *AWS Cloud Practitioner* certification and the *AWS Solutions Architect Associate* certification. I was able to keep costs to a minimum by using AWS's free tier, which allows up to 1 million requests for free per month.

Currently the application can:
- Track the availability of Anmeldung appointments in Bremen
- Send a message to my email in case free appointments are available
- Display the availability of appointments all over Bremen in a website

Future work-in progress functionalities:
- Tracking more cities
- Allowing users to subscribe to a mailing list to receive a notification as soon as an appointment is available
-  Use Amazon API Gateway along with Lambda functions to serve the website instead of S3 in order to make it more dynamic and introduce new functionalities like login.



