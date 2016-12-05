AWS Freezer
===========

Introduction
------------
AWS Freezer is a python based GUI tool to assist in uploading compressed and encrypted archives
to Amazon's AWS Glacier archiving solution. AWS Glacier is a low-cost solution to store large
files that require limited access and redundancy, ideal for large backups. At the time of writing,
the regular cost for Glacier is around $0.007 per Gigabyte of data per month.

Features
--------
### Vaults
AWS Freezer allows creating and managing one or more 'Vaults'. A 'Vault' is an arbitrary collection
of file. Each file in a Vault is called an 'Archive'.
For each vault, AWS Freezer lists the archives present based on current AWS output. If the local
administration and the remote AWS administration differ, AWS Freezer automatically requests a Vault
Inventory job to synchronise the administrations.
Users can manage the archives for each vault. An archive can have one of the following states:
* frozen: the archive is only present in the current vault
* melting: a retrieval request was found, the archive is pending clearance by AWS
* melted: the retrieval request has completed and the archive can be downloaded
* liquid: the archive is present both locally and remote
* local: the archive is only present locally (usually because it is being uploaded)
* invalid: the archive is not present remotely and the local file does not exist either

### Archives
Each archive can be retrieved, removed or disconnected. The first action will cause a retrieval request
to be generated if no such request is present, or it will download the archive if a retrieval request was
found. The second action will remove the remote archive after explicit confirmation. The last action
will only remove the local file of an archive, changing the state from 'liquid' to 'frozen' (or 'melted'
if the retrieval job is still current).

Users can add new archives and select folders and specific files to be added to that archive. Archives
are aggregated using tar and can be compressed using bzip2 or gzip. If an encryption key is set in the
settings dialog, the archive is automatically encrypted using that symmetric encryption key. The
archive description is set based on the provided name, the compression and the encryption, allowing
some means of manual retrieval based on the archive description in case of calamity.

When adding files to archives, filter options allow:
- filtering out files that were already included in another archive
- filtering out common backup file names and generated content (e.g., files ending with '.bak' or object files ending with '.o' and '.pyc')
- filtering out specific paths as set in the settings dialog
- filtering out files that were explicitely (manually) excluded in an earlier stage

The backup filter is enabled by default.

Setup
-----
Upon first invocation, AWS Freezer requests some AWS API settings. To prepare for this, execute the following
actions:
- create an AWS user using AWS IAM that is allowed access to AWS Glacier, AWS SNS and AWS SQS
- note down the AWS user account id, AWS access key and AWS secret key and the AWS region where you want to operate
  vaults
- create a SNS topic to which all Vault request will be posted. Note down the ARN of this SNS topic
- create an SQS queue and from the SQS queue subscribe the SNS topic. This step requires adding specific
  privileges to the SQS queue poster and AWS has a feature to automatically deal with this. Make sure the
  AWS user has read access to this queue and note down the HTTPS end-point of the SQS queue.

Enter the requested values in the settings dialog of AWS Freezer. These values are stored in the SQLite database
associated with AWS Freezer (freezer.db).

Next, proceed to the Encryption tab of the settings dialog. Choose an algorithm and press the 'Create Key' button
to create a new symmetric key for encryption. Amazon recommends encrypting any and all data that is stored on
AWS Glacier. To enable retrieval in case of catastrophic breakdown of local infrastructure, it is recommended to
store the encryption key in a safe place. Without the key, the AWS Glacier archives are useless. Double click on
a key to get the JSON encoded output in the bottom text field. Paste a JSON encoded key in that field and press
the 'Import' button to import an external key.

Dialogs
-------
### Main Dialog
The main dialog displays a list of vaults. This list is retrieved dynamically from AWS and matched with the local
administration. The toolbar allows the following actions:
- create a new vault
- open the vault dialog
- remove a vault

Clicking once on a vault row displays that vaults information in the right viewport. Double click on a row to open
the vault dialog.

Vaults have unique names with a restricted set of characters. Only empty vaults can be removed, so it is normally
safe to press the 'remove vault' toolbar button.

The menu options allow:
- opening the settings dialog (see settings dialog)
- exitting the tool
- viewing all current jobs (see job dialog)
- viewing all files stored in the various archives (see file dialog)

### Vault Dialog
The vault dialog displays all archives available in a vault. This includes archives uploaded through other means,
although interfacing with such archives is limited.
For each archive, it lists the local archive ID, its size, the number of files inside the archive, when it was
created (as determined by the vault inventory of AWS), the archive description (usually containing compression
and encryption information) and the current status of the archive (see above).

The toolbar allows the following actions:
- create a new archive using the archive dialog
- remove an archive (requiring an explicit confirmation sentence: 'I am sure')
- disconnecting an archive (remove the local file only)
- downloading an archive (requesting retrieval or actual retrieval)
- requesting an explicit vault inventory
- closing the dialog

Double clicking on an archive row opens the archive dialog.

### Archive Dialog
The archive dialog features:
- a convenient toolbar
- an archive description field. Additional text is added to this description upon creation (encryption, compression)
- a manual filter option allowing a RegEx expression
- an output selection
- a selected files summary label
- a contents overview

For existing archives, several options are not applicable as the archive cannot be changed.

The toolbar allows:
- adding new files to the archive selection
- adding new folders to the archive selection. Folder content is added recursively.
- applying the archive settings (i.e.: create the archive and upload it)
- filtering all files that are already 'frozen'
- filtering all files that are considered 'backups' or 'generated'. This filters files containing either of the following
  regular expressions: "~$", "\.o$", "\.pyc$", "\.bak$", "\.Po?$", "^#.*#$", "^~"
- filtering all files matching one of the exclude expressions in the settings dialog
- filtering all files that were manually excluded at an earlier point in time
- removing from this selection all files that are currently unselected

The filters toggle the selection state of the files and keep the files in the overview.
Pressing the apply button will close the dialog, aggregate, compress and encrypt the files and upload the result to
AWS Glacier.

A file is defined as a combination of filename, filesize and SHA256 hash. Copies of files in different paths are
considered 'the same' and only the path of the last archive including a specific file is displayed in this overview.

Please note that if copies of files exist inside a different folder and archive and are filtered out, they are
of course not available in the archive when the archive is reconstructed. If a folder contains a few copies that
were excluded based on the fact that these copies were already frozen, they will appear to be missing when the
containing folder is reconstructed. It will be difficult to track the origin of these missing files and in such
cases (when copies appear sparsely inside a folder) it is recommended to archive the copy as well

### Settings Dialog
The Settings Dialog allows setting the AWS credentials, creating and selecting encryption keys and setting default filter
exclusion paths. These settings are stored in the associated SQLite database and override any command line options.

### Job Dialog
The job dialog displays a list of current jobs as available on AWS.

### File Dialog
The file dialog lists all files that were included in an active archive. Files no longer included in any archive are
automatically removed during database maintenance.

Command Line Options
--------------------
AWS Freezer supports the following command line options:
'--help' prints the command line options
'--verbose' displays debug messages
'--trace <list of modules>' restricts debug messages to specific modules
'--threads <num>' sets the maximum number of threads used (excluding GUI and DB threads)

'--no-gui' allows running the tool in daemon mode (see below)
'--config <file>' loads and applies the specified configuration file (default: 'freezer.conf')
'--database <file>' uses the specified file as SQLite database

'--accountid <id>' sets the account ID used for AWS interfacing
'--region <AWS region>' sets the AWS region for the vaults
'--access-key <key>' sets the AWS access key
'--secret-key <key>' sets the required AWS secret key
'--chunk-size <size>' sets the default chunk size used for uploading archives
'--queue <queue URL>' sets the AWS SQS queue poll URL
'--poll-time <secs>' sets the AWS SQS queue polling time (see AWS documentation for valid values)

The values provided are overridden by values stored inside the SQLite database. Using the AWS values on the
command line only makes sense if the SQLite database is empty, for example when using the tool in daemon mode (see below).

Daemon Use
----------
Because jobs take some time to complete and the GUI might not be open at the time of completion, AWS Freezer
has a convenient '--no-gui' command line option. When using this option, the GUI is not drawn and the
tool will effectively only listen to the associated AWS SQS queue for new messages. When a new job has
completed, the tool will automatically download the associated file.
When using this mode, the tool will open-and-close database connections for each activity, which prevents
locking the database for prolonged use. This would allow running the daemon on a server using the same
database file as a GUI front-end elsewhere. The GUI front-end will lock the database, but once it is
closed, the daemon back-end can use the database when and if required. The only effective DB change is
setting the 'executed' date for a specific job if a file is retrieved successfully.

Alternatively, you can run the daemon using an SQLite database containing only the encryption keys and
archive information and no settings or files. This dramatically reduces the size of the database.
The tool will automatically download files based on their description, applying the keys as defined for
each archive.

Encryption
----------
AWS Freezer uses a streaming encryption based on the selected encryption key and the CBC streaming encryption
method. Each frozen archive is constructed as follows:
- a random IV block (containing 8 or 16 bytes depending on the cipher block size)
- a random byte designating the random-header-length (RHL)
- a header containing random bytes
- the aggregated and compressed file

The IV block is not encrypted and can be removed from the archive after retrieval. Using this IV, the
rest of the file is encrypted during upload and download, including the random RHL byte and the random header.
Local files are never encrypted; encryption is completely transparent with AWS Freezer.

Development
-----------
AWS Freezer was developed using Python 2.7 on a Ubuntu workstation. It requires several supporting libraries:
- sqlite3
- shutil
- boto3
- hashlib
- Gtk3 (GObject)

It features a multi-thread controller interfacing with a local SQLite database, remote AWS features (Glacier, SQS)
and a local GUI thread.
