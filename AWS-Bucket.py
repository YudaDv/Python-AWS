import uuid
import boto3

def create_bucket_name(bucket_prefix):
    """
    unique s3-bucket name
    """
    return ''.join([bucket_prefix, str(uuid.uuid4())])

def create_bucket(bucket_prefix, s3_connection):
    """
    creat bucket on any region
    """
    session = boto3.session.Session()
    current_region = session.region_name
    bucket_name = create_bucket_name(bucket_prefix)
    bucket_response = s3_connection.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={
        'LocationConstraint': current_region})
    print(bucket_name, current_region)
    return bucket_name, bucket_response

def create_temp_file(size, file_name, file_content):
    """
    randomized number with first 6 characters in hex representation .
    """
    random_file_name = ''.join([str(uuid.uuid4().hex[:6]), file_name])
    with open(random_file_name, 'w') as f:
        f.write(str(file_content) * size)
    return random_file_name

def copy_to_bucket(bucket_from_name, bucket_to_name, file_name):
    """
    copy file from two buckets
    """
    copy_source = {
        'Bucket': bucket_from_name,
        'Key': file_name
    }
    s3_resource.Object(bucket_to_name, file_name).copy(copy_source)

def enable_bucket_versioning(bucket_name):
    """
    enable ver for bucket
    """
    bkt_versioning = s3_resource.BucketVersioning(bucket_name)
    bkt_versioning.enable()
    print(bkt_versioning.status)

def delete_all_objects(bucket_name):
    """
    delete all objects
    """
    res = []
    bucket=s3_resource.Bucket(bucket_name)
    for obj_version in bucket.object_versions.all():
        res.append({'Key': obj_version.object_key,
                    'VersionId': obj_version.id})
    print(res)
    bucket.delete_objects(Delete={'Objects': res})


                            ##  code  ##


s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')

# creating two buckets, the first with a "client" connection type
# and the second with a "resource" connection type
try:
    first_bucket_name, first_response = create_bucket(
        bucket_prefix='firstpythonbucket',
        s3_connection=s3_resource.meta.client)
except Exception as e:
    print("An exception has occurred:", type(e).__name__)

try:
    second_bucket_name, second_response = create_bucket(
        bucket_prefix='secondpythonbucket', s3_connection=s3_resource)
except Exception as e:
    print("An exception has occurred:", type(e).__name__)


# creating a file by calling to the "create_temp_file" function:
first_file_name = create_temp_file(300, 'firstfile.txt', 'f')

# uploading the first file to the first bucket
first_bucket = s3_resource.Bucket(name=first_bucket_name)
first_object = s3_resource.Object(
    bucket_name=first_bucket_name, key=first_file_name)
try:
    first_object.upload_file(first_file_name)
except Exception as e:
    print("An exception has occurred:", type(e).__name__)

# downloading the first file that we just uploaded
try:
    s3_resource.Object(first_bucket_name, first_file_name).download_file(
        f'/tmp/{first_file_name}')
except Exception as e:
    print("An exception has occurred:", type(e).__name__)

# copying the first file from the first bucket to the second bucket
copy_to_bucket(first_bucket_name, second_bucket_name, first_file_name)

# deleting the file we just copied to the second bucket
s3_resource.Object(second_bucket_name, first_file_name).delete()

# creating a new file in the first bucket and making it public:
second_file_name = create_temp_file(400, 'secondfile.txt', 's')
second_object = s3_resource.Object(first_bucket.name, second_file_name)
second_object.upload_file(second_file_name, ExtraArgs={
                          'ACL': 'public-read'})

# loading the file's ACL into a variable, then showing it:
second_object_acl = second_object.Acl()
print(second_object_acl.grants)

# changing the file's premissions to privte again:
response = second_object_acl.put(ACL='private')
print(second_object_acl.grants)

# creating another file in the first bucket and encrypting it:
third_file_name = create_temp_file(300, 'thirdfile.txt', 't')
third_object = s3_resource.Object(first_bucket_name, third_file_name)
third_object.upload_file(third_file_name, ExtraArgs={
                         'ServerSideEncryption': 'AES256'})
print(third_object.server_side_encryption)

# re-uploading the third file again but as a different storage class
# (changes the way the file is accessed)
third_object.upload_file(third_file_name, ExtraArgs={
                         'ServerSideEncryption': 'AES256',
                         'StorageClass': 'STANDARD_IA'})
third_object.reload()
print(third_object.storage_class)

# enables versioning of files in the first
# bucket by calling to a previously configured function
enable_bucket_versioning(first_bucket_name)

s3_resource.Object(first_bucket_name, second_file_name).upload_file(
    second_file_name)
print(s3_resource.Object(first_bucket_name, first_file_name).version_id)

# printing all bucket names using the s3 resource
for bucket in s3_resource.buckets.all():
    print(bucket.name)

# printing all bucket names using the s3 client:
for bucket_dict in s3_resource.meta.client.list_buckets().get('Buckets'):
    print(bucket_dict['Name'])

# two methods for printing all of the file names in the first bucket
for obj in first_bucket.objects.all():
    print(obj.key)

for obj in first_bucket.objects.all():
    subsrc = obj.Object()
    print(obj.key, obj.storage_class, obj.last_modified,
          subsrc.version_id, subsrc.metadata)

# calling a previously configured function that deletes all files in the bucket:
try:
    delete_all_objects(first_bucket_name)
except Exception as e:
    print("An exception has occurred:", type(e).__name__)

# uploading an alreadt existing file to the second bucket to see what happens in
# a bucket that is not version enabled (it's version will be null)
s3_resource.Object(second_bucket_name, first_file_name).upload_file(
    first_file_name)
try:
    delete_all_objects(second_bucket_name)
except Exception as e:
    print("An exception has occurred:", type(e).__name__)

# deleting the fisrt & second bucket
try:
    s3_resource.Bucket(first_bucket_name).delete()
    s3_resource.meta.client.delete_bucket(Bucket=second_bucket_name)
except Exception as e:
    print("An exception has occurred:", type(e).__name__)
