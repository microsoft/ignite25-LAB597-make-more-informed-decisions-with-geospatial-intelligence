$roles= @('GeoCatalog Administrator')

foreach ($role in $roles) {
New-AzRoleAssignment -SignInName '@lab.CloudPortalCredential(User1).Username' -RoleDefinitionName $role -Scope /subscriptions/37d1391e-71d7-4e07-ba62-3b5d8d4e5fbd/resourceGroups/Lab597_GeoCatalog
}
