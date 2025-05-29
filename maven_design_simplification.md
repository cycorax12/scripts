
# 📘 Maven Design Simplification: From BOM to Clean Parent POM

## 🎯 Objective

We are migrating from a tightly coupled BOM-based structure (`component-properties`) to a **clean, scalable Maven structure** using a **central `parent-pom`** for third-party dependency management only. This design eliminates circular dependency issues and enables independent module versioning, simplifying development and release workflows.

---

## 🔍 Problem With Previous Structure

### ❌ Legacy Design

```
component-properties (CP)
├── Manages third-party deps
├── Manages client1, client2 versions (internal)
│
├── Imported by client1, client2
```

### 🔄 Version Loop Problem

Updating `client1` requires a CP update → which triggers `client2` rebuild → which again changes CP.  
This causes a **cyclical version upgrade loop**:

```
client1 → CP → client2 → CP → client1 ...
```

---

## 🧱 New Structure Overview

We now introduce a **lean design** with:

- A **`parent-pom`** that manages only third-party versions.
- **No CP/BOM** that manages internal module versions.
- All clients **extend `parent-pom`** directly.
- Internal dependencies (like `client1` using `client2`) are declared **explicitly with fixed versions**.

---

## ✅ New Module Structure

```
parent-pom
├── Central 3rd-party dependency management
├── Plugin configs (compiler, surefire, etc.)

client1
├── <parent> = parent-pom
├── Declares dependencies explicitly (e.g., client2)

client2
├── <parent> = parent-pom
```

---

### 🧩 `parent-pom.xml`

```xml
<project>
  <groupId>com.myorg</groupId>
  <artifactId>parent</artifactId>
  <version>1.0.0</version>
  <packaging>pom</packaging>

  <dependencyManagement>
    <dependencies>
      <dependency>
        <groupId>org.apache.commons</groupId>
        <artifactId>commons-lang3</artifactId>
        <version>3.12.0</version>
      </dependency>
      <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>2.15.2</version>
      </dependency>
    </dependencies>
  </dependencyManagement>

  <build>
    <pluginManagement>
      <plugins>
        <plugin>
          <groupId>org.apache.maven.plugins</groupId>
          <artifactId>maven-compiler-plugin</artifactId>
          <version>3.11.0</version>
          <configuration>
            <source>17</source>
            <target>17</target>
          </configuration>
        </plugin>
      </plugins>
    </pluginManagement>
  </build>
</project>
```

---

### 🔧 Example `client1/pom.xml`

```xml
<project>
  <parent>
    <groupId>com.myorg</groupId>
    <artifactId>parent</artifactId>
    <version>1.0.0</version>
  </parent>

  <artifactId>client1</artifactId>
  <version>1.2.0</version>

  <dependencies>
    <dependency>
      <groupId>org.apache.commons</groupId>
      <artifactId>commons-lang3</artifactId>
    </dependency>

    <!-- Explicit internal dependency -->
    <dependency>
      <groupId>com.myorg</groupId>
      <artifactId>client2</artifactId>
      <version>1.1.0</version>
    </dependency>
  </dependencies>
</project>
```

---

## 🔁 Dependency Workflow Comparison

### ❌ Before: BOM Creates Coupling and Cycles

```
               ┌────────────┐
               │ component- │
               │ properties │
               └─────┬──────┘
                     ↓
      ┌────────────┐   ┌────────────┐
      │  client1   │ ← │  client2   │
      └────────────┘   └────────────┘
         ↑
         └──── depends on BOM, which depends back ─────┘
```

---

### ✅ After: Clean Parent, Explicit Internal Dependencies

```
               ┌──────────────┐
               │  parent-pom  │
               │ (3rd-party)  │
               └──────┬───────┘
                      ↓
    ┌────────────┐     ┌────────────┐
    │  client1   │     │  client2   │
    └────┬───────┘     └────┬───────┘
         │                 │
         └─ depends on ────┘ (explicit, if needed)
```

---

## ✅ Updated Design Diagram (with Team Actions)

```
                       ┌──────────────────┐
                       │   parent-pom     │
                       │ (3rd-party deps, │
                       │ plugins, config) │
                       └────────┬─────────┘
                                ↓
         ┌────────────────────────────┐
         │     Developer Actions      │
         └────────────────────────────┘
                ▼               ▼
      ┌─────────────────┐   ┌─────────────────┐
      │    client1      │   │    client2      │
      │ ─────────────── │   │ ─────────────── │
      │ - Set <parent>  │   │ - Set <parent>  │
      │   to parent-pom │   │   to parent-pom │
      │ - Remove CP/BOM │   │ - Remove CP/BOM │
      │ - Declare any   │   │ - Declare any   │
      │   internal deps │   │   internal deps │
      └─────────────────┘   └─────────────────┘
                │                  │
                ▼                  ▼
      ┌────────────────────────────────────┐
      │    DevOps/CI/CD Pipeline Actions   │
      └────────────────────────────────────┘
      │ - Stop auto-upgrading client versions
      │ - Decouple version bump logic
      │ - Build/test each module independently
      │ - Only tag/release changed clients
      └────────────────────────────────────┘
```

---

## 📋 Migration Action Plan

### 👩‍💻 Developer Checklist

| Step | Action |
|------|--------|
| ✅ 1 | Remove CP/BOM from `pom.xml` |
| ✅ 2 | Set `<parent>` to `parent-pom` |
| ✅ 3 | Declare internal module dependencies explicitly with versions |
| ✅ 4 | Do **not** rely on inherited internal versions |
| ✅ 5 | Test module independently before pushing changes |

---

### 🧑‍💻 DevOps/CI Checklist

| Step | Action |
|------|--------|
| ✅ 1 | Update CI/CD pipelines to decouple module versioning |
| ✅ 2 | Remove any auto-version bump logic tied to shared BOM |
| ✅ 3 | Ensure modules are tagged/released independently |
| ✅ 4 | Treat `parent-pom` as an independent, rarely changed artifact |
| ✅ 5 | Use Maven plugins (`versions-maven-plugin`, `maven-release-plugin`) or `jgitver` for scoped version control |

---

## 🚀 Benefits of the New Design

| Benefit                     | Explanation                                                 |
|-----------------------------|-------------------------------------------------------------|
| ✅ No version loops         | Each module can upgrade without triggering a cycle         |
| ✅ Explicit dependencies    | Modules clearly declare what they rely on                  |
| ✅ Independent releases     | Teams can own and release their services autonomously       |
| ✅ Simpler CI/CD pipelines  | Only changed clients are rebuilt and tagged                 |
| ✅ Better scalability       | Easy to grow and onboard new modules                        |
