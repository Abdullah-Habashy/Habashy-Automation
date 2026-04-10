resolve = Resolve()
projectManager = resolve:GetProjectManager()
project = projectManager:GetCurrentProject()

print("=" .. string.rep("=", 50))
print("✅ SUCCESS! Lua Script is running inside Resolve!")
print("=" .. string.rep("=", 50))

if project then
    print("📁 Current Project: " .. project:GetName())
    
    -- Create a test bin
    mediaPool = project:GetMediaPool()
    root = mediaPool:GetRootFolder()
    
    -- Add a folder
    newFolder = mediaPool:AddSubFolder(root, "Test_Bin_From_Lua")
    
    if newFolder then
        print("📂 Created folder 'Test_Bin_From_Lua' in Media Pool")
    else
        print("⚠️ Could not create bin (maybe already exists)")
    end
else
    print("❌ No project open")
end

print("=" .. string.rep("=", 50))
print("You can now automate your workflow using Lua!")
