import json
import boto3
import uuid
import base64
from datetime import datetime

# ===== CONFIGURATION =====
DYNAMODB_TABLE_NAME = 'megha-jobapplication-portal-dynamodb'
S3_RESUME_BUCKET = 'megha-jobapplication-bucket'  # Your bucket name
S3_RESUME_PREFIX = 'resumes/'
S3_REGION = 'ap-south-1'  # Your bucket region

# Direct S3 URL base (public access)
S3_BASE_URL = f'https://{S3_RESUME_BUCKET}.s3.{S3_REGION}.amazonaws.com'

# AWS Clients
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE_NAME)
s3_client = boto3.client('s3', region_name=S3_REGION)


def lambda_handler(event, context):
    """
    Main Lambda handler - routes requests based on HTTP method and path.
    Handles REST API v1, HTTP API v2, Lambda Function URLs, and Lambda Console test events.
    """
    print("FULL EVENT: " + json.dumps(event))

    # ===== EXTRACT METHOD AND PATH FROM ANY EVENT FORMAT =====
    http_method = ''
    path = ''

    # Format 1: REST API (v1) - has httpMethod at top level
    if event.get('httpMethod'):
        http_method = event['httpMethod']
        path = event.get('resource', '') or event.get('path', '')

    # Format 2: HTTP API (v2) / Function URL - has requestContext.http
    elif event.get('requestContext', {}).get('http', {}).get('method'):
        http_method = event['requestContext']['http']['method']
        path = event.get('rawPath', '') or event['requestContext']['http'].get('path', '')

    # Format 3: HTTP API v2 alternate - has routeKey like "POST /applications"
    elif event.get('routeKey'):
        route_key = event['routeKey']
        if ' ' in route_key:
            http_method, path = route_key.split(' ', 1)
        else:
            path = route_key
            http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')

    # Format 4: Direct Lambda console test - user passes method/path in body
    elif event.get('method'):
        http_method = event['method']
        path = event.get('path', '/applications')

    # Normalize: strip stage prefix (e.g., /prod/applications -> /applications)
    if '/applications' in path:
        path = path[path.index('/applications'):]

    # If still empty, check if event itself is application data (direct POST test)
    if not path and not http_method:
        if event.get('firstName') or event.get('email'):
            http_method = 'POST'
            path = '/applications'
            event['body'] = json.dumps(event)

    http_method = http_method.upper()

    # Extract path parameters
    path_parameters = event.get('pathParameters', {}) or {}

    print(f"Resolved -> Method: {http_method}, Path: {path}, PathParams: {path_parameters}")

    # Handle CORS preflight
    if http_method == 'OPTIONS':
        return build_response(200, {'message': 'OK'})

    try:
        # Get application ID from path parameters or URL path
        application_id = ''
        if path_parameters.get('id'):
            application_id = path_parameters['id']
        elif path_parameters.get('applicationId'):
            application_id = path_parameters['applicationId']
        elif path_parameters.get('proxy'):
            # strip leading slash if present e.g. "proxy": "some-uuid"
            application_id = path_parameters['proxy'].strip('/')
        elif '/applications/' in path:
            # Extract from raw path e.g. /applications/some-uuid
            part = path.split('/applications/')[-1].strip('/')
            if part:  # make sure it's not empty (i.e. not just /applications/)
                application_id = part

        print(f"Extracted application_id: '{application_id}'")

        # ===== ROUTING =====
        if path == '/applications' and http_method == 'POST':
            body = get_body(event)
            return create_application(body)

        elif path == '/applications' and http_method == 'GET':
            return get_all_applications()

        elif application_id and http_method == 'GET':
            return get_application(application_id)

        elif application_id and http_method == 'PUT':
            body = get_body(event)
            return update_application(application_id, body)

        elif application_id and http_method == 'DELETE':
            return delete_application(application_id)

        else:
            return build_response(404, {
                'message': 'Route not found',
                'debug': {
                    'method': http_method,
                    'path': path,
                    'pathParams': path_parameters,
                    'eventKeys': list(event.keys())
                }
            })

    except Exception as e:
        print(f"Error: {str(e)}")
        return build_response(500, {'message': f'Internal server error: {str(e)}'})


def get_body(event):
    """Extract and parse the request body from any event format."""
    body = event.get('body', '{}')

    if body is None:
        body = '{}'

    if isinstance(body, str):
        if event.get('isBase64Encoded'):
            body = base64.b64decode(body).decode('utf-8')
        return json.loads(body)

    if isinstance(body, dict):
        return body

    return {}


# ===== CRUD OPERATIONS =====

def create_application(body):
    """
    POST /applications
    Creates a new job application and uploads resume to S3.
    """
    required_fields = ['firstName', 'lastName', 'email', 'position', 'experience']
    for field in required_fields:
        if not body.get(field):
            return build_response(400, {'message': f'Missing required field: {field}'})

    application_id = str(uuid.uuid4())

    # Handle resume upload to S3
    resume_url = ''
    resume_s3_key = ''

    if body.get('resume') and body['resume'].get('data'):
        resume_data = body['resume']
        file_extension = resume_data.get('filename', 'file.pdf').split('.')[-1]
        resume_s3_key = f"{S3_RESUME_PREFIX}{application_id}/{resume_data.get('filename', 'resume.' + file_extension)}"

        file_content = base64.b64decode(resume_data['data'])

        s3_client.put_object(
            Bucket=S3_RESUME_BUCKET,
            Key=resume_s3_key,
            Body=file_content,
            ContentType=resume_data.get('contentType', 'application/pdf')
        )

        # Use direct public URL instead of presigned URL
        resume_url = f"{S3_BASE_URL}/{resume_s3_key}"

    item = {
        'applicationid': application_id,   # partition key — must match DynamoDB table definition
        'applicationId': application_id,   # also store camelCase for API responses
        'firstName': body['firstName'],
        'lastName': body['lastName'],
        'email': body['email'],
        'phone': body.get('phone', ''),
        'dob': body.get('dob', ''),
        'address': body.get('address', ''),
        'position': body['position'],
        'experience': body['experience'],
        'skills': body.get('skills', ''),
        'education': body.get('education', ''),
        'linkedin': body.get('linkedin', ''),
        'portfolio': body.get('portfolio', ''),
        'coverLetter': body.get('coverLetter', ''),
        'resumeS3Key': resume_s3_key,
        'resumeUrl': resume_url,
        'status': 'New',
        'notes': '',
        'appliedAt': datetime.utcnow().isoformat(),
        'updatedAt': datetime.utcnow().isoformat()
    }

    table.put_item(Item=item)

    return build_response(201, {
        'message': 'Application submitted successfully',
        'applicationId': application_id
    })


def get_all_applications():
    """
    GET /applications
    Returns all job applications.
    """
    response = table.scan()
    applications = response.get('Items', [])

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        applications.extend(response.get('Items', []))

    applications.sort(key=lambda x: x.get('appliedAt', ''), reverse=True)

    # Rebuild public URLs for resumes (in case bucket/region changed)
    for app in applications:
        if app.get('resumeS3Key'):
            app['resumeUrl'] = f"{S3_BASE_URL}/{app['resumeS3Key']}"
        # Normalize key name for frontend (table uses lowercase 'applicationid')
        if 'applicationid' in app and 'applicationId' not in app:
            app['applicationId'] = app['applicationid']

    return build_response(200, {'applications': applications, 'count': len(applications)})


def get_application(application_id):
    """
    GET /applications/{id}
    Returns a single application by ID.
    """
    response = table.get_item(Key={'applicationid': application_id})
    item = response.get('Item')

    if not item:
        scan_response = table.scan(
            FilterExpression='applicationId = :aid OR applicationid = :aid',
            ExpressionAttributeValues={':aid': application_id}
        )
        items = scan_response.get('Items', [])
        item = items[0] if items else None

    if not item:
        return build_response(404, {'message': 'Application not found'})

    if item.get('resumeS3Key'):
        item['resumeUrl'] = f"{S3_BASE_URL}/{item['resumeS3Key']}"

    return build_response(200, item)


def update_application(application_id, body):
    """
    PUT /applications/{id}
    Updates an existing application.
    """
    response = table.get_item(Key={'applicationid': application_id})
    if not response.get('Item'):
        # Fallback scan for records with mismatched key casing
        scan_response = table.scan(
            FilterExpression='applicationId = :aid OR applicationid = :aid',
            ExpressionAttributeValues={':aid': application_id}
        )
        items = scan_response.get('Items', [])
        if not items:
            return build_response(404, {'message': 'Application not found'})
        # Use the real partition key from the found item
        application_id = items[0].get('applicationid') or items[0].get('applicationId') or application_id

    update_fields = ['firstName', 'lastName', 'email', 'phone', 'position',
                     'experience', 'skills', 'education', 'status', 'notes',
                     'linkedin', 'portfolio', 'address', 'coverLetter']

    update_expression_parts = []
    expression_values = {}
    expression_names = {}

    for field in update_fields:
        if field in body:
            safe_key = f'#{field}'
            val_key = f':{field}'
            update_expression_parts.append(f'{safe_key} = {val_key}')
            expression_values[val_key] = body[field]
            expression_names[safe_key] = field

    update_expression_parts.append('#updatedAt = :updatedAt')
    expression_values[':updatedAt'] = datetime.utcnow().isoformat()
    expression_names['#updatedAt'] = 'updatedAt'

    update_expression = 'SET ' + ', '.join(update_expression_parts)

    table.update_item(
        Key={'applicationid': application_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_values,
        ExpressionAttributeNames=expression_names
    )

    return build_response(200, {'message': 'Application updated successfully'})


def delete_application(application_id):
    """
    DELETE /applications/{id}
    Deletes an application and its resume from S3.
    """
    # Try direct get_item first (fast path)
    response = table.get_item(Key={'applicationid': application_id})
    item = response.get('Item')

    # If not found, the record might have been created before key normalization
    # Scan for it as fallback
    if not item:
        scan_response = table.scan(
            FilterExpression='applicationId = :aid OR applicationid = :aid',
            ExpressionAttributeValues={':aid': application_id}
        )
        items = scan_response.get('Items', [])
        if items:
            item = items[0]
            # Use the actual partition key value stored in DynamoDB
            application_id = item.get('applicationid') or item.get('applicationId') or application_id

    if not item:
        return build_response(404, {'message': f'Application not found: {application_id}'})

    if item.get('resumeS3Key'):
        try:
            s3_client.delete_object(Bucket=S3_RESUME_BUCKET, Key=item['resumeS3Key'])
        except Exception as e:
            print(f"Warning: Could not delete resume from S3: {str(e)}")

    table.delete_item(Key={'applicationid': application_id})

    return build_response(200, {'message': 'Application deleted successfully'})


# ===== HELPER =====

def build_response(status_code, body):
    """Builds API Gateway compatible response with CORS headers."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body, default=str)
    }
