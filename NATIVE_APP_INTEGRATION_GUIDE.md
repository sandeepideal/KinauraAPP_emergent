# Native App Implementation Guide
## KinAura Content Synchronization for iOS & Android

### Overview
This guide shows mobile developers how to implement the KinAura content synchronization system to get **immediate updates** without requiring app store submissions.

---

## 🔧 API Integration

### 1. Content Version Checking
```javascript
// Check current content version
GET /api/content/version

Response:
{
  "global_version": "abc123...",
  "last_updated": "2024-12-21T15:30:00Z",
  "content_types": {
    "services": {
      "content_type": "services", 
      "last_modified": "2024-12-21T15:25:00Z",
      "content_version": "def456...",
      "content_hash": "7b2a8f..."
    },
    "products": { ... },
    "service_groups": { ... }
  }
}
```

### 2. Change Detection
```javascript
// Check for changes since last sync
GET /api/content/changes?since_version=YOUR_STORED_VERSION&since_timestamp=2024-12-21T14:00:00Z

Response:
{
  "has_changes": true,
  "global_version": "xyz789...",
  "changed_content": {
    "services": {
      "content_type": "services",
      "last_modified": "2024-12-21T15:25:00Z",
      "content_hash": "new_hash..."
    }
  }
}
```

### 3. Enhanced Data Fetching
```javascript
// Get services with sync metadata
GET /api/services/sync?if_modified_since=2024-12-21T14:00:00Z

Response:
{
  "services": [
    {
      "id": "service-123",
      "name": "Advanced Longevity Protocol",
      "price": 450.00,
      "updated_at": "2024-12-21T15:25:00Z",
      "content_version": "uuid-here",
      // ... other service fields
    }
  ],
  "count": 5,
  "last_updated": "2024-12-21T15:25:00Z",
  "content_hash": "abc123...",
  "cache_ttl": 300
}
```

---

## 📱 Mobile Implementation Patterns

### iOS (Swift) Example
```swift
class ContentSyncManager {
    private let apiUrl = "https://your-kinaura-api.com/api"
    private var currentVersion: String?
    private var lastSyncTime: Date?
    
    // Check for content updates
    func checkForUpdates() async -> Bool {
        guard let url = URL(string: "\(apiUrl)/content/changes") else { return false }
        
        var components = URLComponents(url: url, resolvingAgainstBaseURL: false)
        var queryItems: [URLQueryItem] = []
        
        if let version = currentVersion {
            queryItems.append(URLQueryItem(name: "since_version", value: version))
        }
        
        if let timestamp = lastSyncTime {
            let formatter = ISO8601DateFormatter()
            queryItems.append(URLQueryItem(name: "since_timestamp", value: formatter.string(from: timestamp)))
        }
        
        components?.queryItems = queryItems
        
        do {
            let (data, _) = try await URLSession.shared.data(from: components?.url ?? url)
            let response = try JSONDecoder().decode(ContentChangesResponse.self, from: data)
            
            if response.hasChanges {
                await syncContent(changedContent: response.changedContent)
                currentVersion = response.globalVersion
                lastSyncTime = Date()
                
                // Store in UserDefaults for persistence
                UserDefaults.standard.set(currentVersion, forKey: "content_version")
                UserDefaults.standard.set(lastSyncTime, forKey: "last_sync_time")
                
                return true
            }
            
            return false
        } catch {
            print("Content check failed: \(error)")
            return false
        }
    }
    
    // Sync specific content types
    private func syncContent(changedContent: [String: ContentSyncStatus]) async {
        for (contentType, _) in changedContent {
            switch contentType {
            case "services":
                await syncServices()
            case "products":
                await syncProducts()
            case "service_groups":
                await syncServiceGroups()
            default:
                break
            }
        }
    }
    
    // Sync services data
    private func syncServices() async {
        guard let url = URL(string: "\(apiUrl)/services/sync") else { return }
        
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let response = try JSONDecoder().decode(ServicesSyncResponse.self, from: data)
            
            // Update local database/cache
            await CoreDataManager.shared.updateServices(response.services)
            
            print("✅ Services synced: \(response.count) items")
        } catch {
            print("❌ Services sync failed: \(error)")
        }
    }
}

// Background sync setup
extension ContentSyncManager {
    func startBackgroundSync() {
        // Check for updates every 5 minutes when app is active
        Timer.scheduledTimer(withTimeInterval: 300, repeats: true) { _ in
            Task {
                await self.checkForUpdates()
            }
        }
    }
    
    // Check for updates when app becomes active
    func setupAppStateObserver() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(appDidBecomeActive),
            name: UIApplication.didBecomeActiveNotification,
            object: nil
        )
    }
    
    @objc private func appDidBecomeActive() {
        Task {
            await checkForUpdates()
        }
    }
}
```

### React Native Example
```javascript
import { useEffect, useState, useRef } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

const useContentSync = () => {
  const [isSync
  const API_URL = 'https://your-kinaura-api.com/api';
  const syncIntervalRef = useRef();

  const checkForUpdates = async () => {
    try {
      // Get stored version and timestamp
      const storedVersion = await AsyncStorage.getItem('content_version');
      const storedTimestamp = await AsyncStorage.getItem('last_sync_time');
      
      // Build query parameters
      const params = new URLSearchParams();
      if (storedVersion) params.append('since_version', storedVersion);
      if (storedTimestamp) params.append('since_timestamp', storedTimestamp);
      
      // Check for changes
      const response = await fetch(`${API_URL}/content/changes?${params}`);
      const data = await response.json();
      
      if (data.has_changes) {
        console.log('📡 Content changes detected:', data.changed_content);
        
        // Sync changed content
        await syncChangedContent(data.changed_content);
        
        // Update stored version and timestamp
        await AsyncStorage.setItem('content_version', data.global_version);
        await AsyncStorage.setItem('last_sync_time', new Date().toISOString());
        
        setSyncStatus('synced');
        setLastSyncTime(new Date());
        
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('❌ Content sync failed:', error);
      setSyncStatus('error');
      return false;
    }
  };

  const syncChangedContent = async (changedContent) => {
    for (const contentType in changedContent) {
      switch (contentType) {
        case 'services':
          await syncServices();
          break;
        case 'products':
          await syncProducts();
          break;
        case 'service_groups':
          await syncServiceGroups();
          break;
      }
    }
  };

  const syncServices = async () => {
    try {
      const response = await fetch(`${API_URL}/services/sync`);
      const data = await response.json();
      
      // Update local storage/database
      await AsyncStorage.setItem('services_data', JSON.stringify(data.services));
      await AsyncStorage.setItem('services_hash', data.content_hash);
      
      console.log('✅ Services synced:', data.count, 'items');
    } catch (error) {
      console.error('❌ Services sync failed:', error);
    }
  };

  // Start periodic sync
  useEffect(() => {
    // Initial sync
    checkForUpdates();
    
    // Set up periodic sync (every 5 minutes)
    syncIntervalRef.current = setInterval(checkForUpdates, 5 * 60 * 1000);
    
    // Cleanup
    return () => {
      if (syncIntervalRef.current) {
        clearInterval(syncIntervalRef.current);
      }
    };
  }, []);

  return {
    syncStatus,
    lastSyncTime,
    manualSync: checkForUpdates
  };
};
```

### Android (Kotlin) Example
```kotlin
class ContentSyncManager(private val context: Context) {
    private val apiUrl = "https://your-kinaura-api.com/api"
    private val prefs = context.getSharedPreferences("content_sync", Context.MODE_PRIVATE)
    private val retrofit = Retrofit.Builder()
        .baseUrl(apiUrl)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    private val apiService = retrofit.create(KinAuraApiService::class.java)
    
    suspend fun checkForUpdates(): Boolean = withContext(Dispatchers.IO) {
        try {
            val storedVersion = prefs.getString("content_version", null)
            val storedTimestamp = prefs.getString("last_sync_time", null)
            
            val response = apiService.getContentChanges(storedVersion, storedTimestamp)
            
            if (response.hasChanges) {
                Log.d("ContentSync", "📡 Content changes detected: ${response.changedContent.keys}")
                
                syncChangedContent(response.changedContent)
                
                prefs.edit()
                    .putString("content_version", response.globalVersion)
                    .putString("last_sync_time", Date().toISOString())
                    .apply()
                
                true
            } else {
                false
            }
        } catch (e: Exception) {
            Log.e("ContentSync", "❌ Content sync failed", e)
            false
        }
    }
    
    private suspend fun syncChangedContent(changedContent: Map<String, ContentSyncStatus>) {
        changedContent.forEach { (contentType, _) ->
            when (contentType) {
                "services" -> syncServices()
                "products" -> syncProducts()
                "service_groups" -> syncServiceGroups()
            }
        }
    }
    
    private suspend fun syncServices() {
        try {
            val response = apiService.getServicesSync()
            
            // Update local database
            AppDatabase.getInstance(context).serviceDao().updateAll(response.services)
            
            Log.d("ContentSync", "✅ Services synced: ${response.count} items")
        } catch (e: Exception) {
            Log.e("ContentSync", "❌ Services sync failed", e)
        }
    }
    
    // Background sync with WorkManager
    fun scheduleBackgroundSync() {
        val syncRequest = PeriodicWorkRequestBuilder<ContentSyncWorker>(
            15, TimeUnit.MINUTES // Minimum interval
        ).build()
        
        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            "content_sync",
            ExistingPeriodicWorkPolicy.KEEP,
            syncRequest
        )
    }
}

class ContentSyncWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result {
        return try {
            val syncManager = ContentSyncManager(applicationContext)
            val hasUpdates = syncManager.checkForUpdates()
            
            if (hasUpdates) {
                // Optionally send local notification about updates
                NotificationHelper.showUpdateNotification(applicationContext)
            }
            
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }
}
```

---

## 🔄 Integration Checklist

### ✅ Required Implementation Steps

1. **Content Version Storage**
   - Store `global_version` locally
   - Store `last_sync_time` timestamp
   - Persist across app launches

2. **Periodic Sync**
   - Check for updates every 5 minutes when active
   - Check when app becomes active
   - Background sync with WorkManager/Background Tasks

3. **Efficient Data Transfer**
   - Use `if_modified_since` parameter
   - Only sync changed content types
   - Implement local caching/database

4. **Error Handling**
   - Retry failed requests
   - Fallback to cached data
   - User-friendly error messages

5. **User Experience**
   - Show sync status (optional)
   - Loading states during sync
   - Offline mode with cached data

---

## 🚀 Results

With this implementation, your KinAura mobile app will:

- **📡 Update content within 1-2 seconds** of admin changes
- **🔄 Work offline** with cached data
- **⚡ Efficient data usage** through incremental sync
- **🎯 Zero app store dependencies** for content updates
- **💾 Minimal storage footprint** with smart caching

---

## 📞 Support

For implementation questions or technical support, contact the KinAura development team.