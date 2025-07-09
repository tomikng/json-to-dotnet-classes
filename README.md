# JSON to C# Class Generator

[![Tests](https://github.com/tomikng/json-to-dotnet-classes/workflows/Tests/badge.svg)](https://github.com/tomikng/json-to-dotnet-classes/actions)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful Python tool that automatically generates strongly-typed C# classes from JSON structures. Perfect for creating DTOs, API models, and data contracts with proper JSON serialization attributes.

## Features

✅ **Automatic Type Detection** - Detects strings, numbers, booleans, dates, arrays, and nested objects  
✅ **Proper Pluralization** - Uses intelligent singularization for array item classes (Activities → Activity)  
✅ **JsonPropertyName Attributes** - Generates proper JSON serialization attributes  
✅ **Nullable Types** - All properties are nullable for robust deserialization  
✅ **Configurable Namespaces** - Customize the generated namespace  
✅ **Records or Classes** - Choose between C# records or traditional classes  
✅ **Separate Files** - Each class generated in its own file for better organization  
✅ **DateTime Detection** - Automatically detects ISO date strings  

## Installation

1. **Clone or download** this repository
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```bash
# Generate classes from a JSON file
python3 json_to_csharp.py data.json
```

This will create a `Generated/` folder with all the C# class files.

### Advanced Usage

```bash
# Customize output directory and namespace
python3 json_to_csharp.py data.json \
  --output Models \
  --namespace MyApp.Models \
  --root-class ApiResponse

# Generate records instead of classes
python3 json_to_csharp.py data.json --records
```

### Command Line Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | `Generated` | Output directory for generated files |
| `--namespace` | `-n` | `Generated.Models` | C# namespace for generated classes |
| `--root-class` | `-r` | `RootDto` | Name of the root class |
| `--records` | | `false` | Generate records instead of classes |
| `--help` | `-h` | | Show help message |

## Examples

### Input JSON
```json
{
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "createdAt": "2023-01-15T10:30:00Z",
      "isActive": true,
      "profile": {
        "age": 30,
        "city": "New York"
      }
    }
  ],
  "totalCount": 1
}
```

### Generated Output

**RootDto.cs**
```csharp
using System.Text.Json.Serialization;
using System;
using System.Collections.Generic;

namespace Generated.Models;

public class RootDto
{
    [JsonPropertyName("users")]
    public List<User>? Users { get; init; }

    [JsonPropertyName("totalCount")]
    public int? TotalCount { get; init; }
}
```

**User.cs**
```csharp
using System.Text.Json.Serialization;
using System;
using System.Collections.Generic;

namespace Generated.Models;

public class User
{
    [JsonPropertyName("id")]
    public int? Id { get; init; }

    [JsonPropertyName("name")]
    public string? Name { get; init; }

    [JsonPropertyName("email")]
    public string? Email { get; init; }

    [JsonPropertyName("createdAt")]
    public DateTime? CreatedAt { get; init; }

    [JsonPropertyName("isActive")]
    public bool? IsActive { get; init; }

    [JsonPropertyName("profile")]
    public Profile? Profile { get; init; }
}
```

**Profile.cs**
```csharp
using System.Text.Json.Serialization;
using System;
using System.Collections.Generic;

namespace Generated.Models;

public class Profile
{
    [JsonPropertyName("age")]
    public int? Age { get; init; }

    [JsonPropertyName("city")]
    public string? City { get; init; }
}
```

## Using Generated Classes

### In Your C# Project

```csharp
using System.Text.Json;
using Generated.Models;

// Deserialize JSON
string jsonString = File.ReadAllText("data.json");
var data = JsonSerializer.Deserialize<RootDto>(jsonString);

// Access strongly-typed properties
var firstUser = data?.Users?.FirstOrDefault();
Console.WriteLine($"User: {firstUser?.Name}, Email: {firstUser?.Email}");
Console.WriteLine($"Age: {firstUser?.Profile?.Age}");
```

### With HttpClient

```csharp
using System.Net.Http.Json;
using Generated.Models;

var httpClient = new HttpClient();
var response = await httpClient.GetFromJsonAsync<RootDto>("https://api.example.com/data");

foreach (var user in response?.Users ?? [])
{
    Console.WriteLine($"{user.Name} - {user.Email}");
}
```

## Type Mapping

| JSON Type | C# Type |
|-----------|---------|
| `string` | `string?` |
| `number` (integer) | `int?` |
| `number` (decimal) | `decimal?` |
| `boolean` | `bool?` |
| `null` | `object?` |
| `array` | `List<T>?` |
| `object` | `CustomClass?` |
| ISO date string | `DateTime?` |

## Smart Naming Conventions

The generator uses intelligent naming conventions while preserving important suffixes and acronyms:

### Property Naming
- **Preserve Acronyms**: `FxLinkResponseID` → `FxLinkResponseID` (keeps ID suffix)
- **Preserve Numbers**: `Level1Split`, `Level2Split` → `Level1Split`, `Level2Split` (prevents duplicates)
- **Pascal Case**: `user_name` → `UserName`, `myProperty` → `MyProperty`

### Class Naming
- **Pluralization**: `activities` → `Activity` class (intelligent singularization for arrays)
- **Preserve Original Names**: Class names maintain their original structure and suffixes

### Code Generation Features
- **Nullable Context**: All files include `#nullable enable` directive for proper nullable reference types
- **Auto-Generated Headers**: Each file includes attribution comments
- **Consistent Formatting**: Clean, readable C# code with proper indentation

## Requirements

- Python 3.8+
- `inflect` library (for proper pluralization)

## Testing

The project includes comprehensive tests to ensure reliability and correctness.

### Running Tests Locally

```bash
# Quick test run
python run_tests.py

# Or run tests manually
pip install -r requirements.txt
python -m pytest test_json_to_csharp.py -v
```

### Test Coverage

The test suite covers:

- ✅ **Type Detection** - All JSON to C# type conversions
- ✅ **Pluralization** - Proper singular/plural handling (Activities → Activity)
- ✅ **Naming Conventions** - PascalCase, DD suffix, str prefix handling
- ✅ **File Generation** - Actual C# file creation and content verification
- ✅ **Nested Objects** - Complex object hierarchies
- ✅ **Arrays** - List handling and item class generation
- ✅ **CLI Interface** - Command line argument processing
- ✅ **Error Handling** - Invalid JSON, missing files, etc.
- ✅ **Integration Tests** - End-to-end workflow testing

### Continuous Integration

The project uses GitHub Actions for automated testing:

- **Multi-platform**: Tests run on Ubuntu, Windows, and macOS
- **Multi-version**: Python 3.8, 3.9, 3.10, 3.11, and 3.12

All tests must pass before code can be merged.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool!

## License

This project is open source. Feel free to use and modify as needed. 