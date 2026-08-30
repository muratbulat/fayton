<#
.SYNOPSIS
    Reports Active Directory group membership counts by department for
    the users currently logged into a list of VMs.

.DESCRIPTION
    For each computer name in the input file, finds the currently
    logged-in user via CIM, looks up that user's AD department and group
    memberships, and exports a per-department / per-group membership
    count to CSV.

.PARAMETER VmListPath
    Path to a text file containing one VM/computer name per line.

.PARAMETER OutputPath
    Path to write the resulting CSV report to.

.PARAMETER Credential
    Optional credential to use for the remote CIM queries and AD lookups.

.EXAMPLE
    .\vm_users_ad.ps1 -VmListPath .\vm_list.txt -OutputPath .\DepartmentGroupCounts.csv

.NOTES
    Get-CimInstance uses WinRM by default, so target machines must have
    PowerShell remoting enabled (Enable-PSRemoting). If your environment
    only allows DCOM, query with
    New-CimSession -ComputerName <vm> -SessionOption (New-CimSessionOption -Protocol Dcom)
    instead.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({ Test-Path -Path $_ -PathType Leaf })]
    [string]$VmListPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [System.Management.Automation.PSCredential]$Credential
)

Import-Module ActiveDirectory -ErrorAction Stop

$vmList = Get-Content -Path $VmListPath
$departmentGroups = @{}

$cimParams = @{}
if ($Credential) {
    $cimParams['Credential'] = $Credential
}

foreach ($vm in $vmList) {
    try {
        $user = Get-CimInstance -ClassName Win32_ComputerSystem -ComputerName $vm -ErrorAction Stop @cimParams |
            Select-Object -ExpandProperty UserName

        if (-not $user) {
            Write-Warning "No logged-in user found for $vm"
            continue
        }

        # Split the domain and username if needed
        $usernameParts = $user.Split('\')
        $username = if ($usernameParts.Length -eq 2) { $usernameParts[1] } else { $user }

        # Get the user's AD information, including department and group memberships
        $adUser = Get-ADUser -Identity $username -Property Department, MemberOf -ErrorAction Stop

        $department = if ($adUser.Department) { $adUser.Department } else { 'Unknown' }

        if (-not $departmentGroups.ContainsKey($department)) {
            $departmentGroups[$department] = @{}
        }

        # Iterate through the groups the user is a member of
        foreach ($group in $adUser.MemberOf) {
            # Resolve the group name from the DistinguishedName
            $groupName = (Get-ADGroup $group).Name

            if (-not $departmentGroups[$department].ContainsKey($groupName)) {
                $departmentGroups[$department][$groupName] = 1
            } else {
                $departmentGroups[$department][$groupName]++
            }
        }
    } catch {
        Write-Error "Error processing VM $vm : $($_.Exception.Message)"
    }
}

# Convert the hashtable to an array of objects for easier sorting and filtering
$results = foreach ($department in $departmentGroups.Keys) {
    foreach ($group in $departmentGroups[$department].Keys) {
        [PSCustomObject]@{
            Department = $department
            GroupName  = $group
            UserCount  = $departmentGroups[$department][$group]
        }
    }
}

# Sort by department (ascending), then by user count within each department (descending)
$sortedResults = $results | Sort-Object Department, @{Expression = 'UserCount'; Descending = $true }

$sortedResults | Export-Csv -Path $OutputPath -NoTypeInformation

Write-Output "Group counts by department have been exported to $OutputPath"
