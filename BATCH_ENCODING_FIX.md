# 批处理文件编码问题修复说明

## 问题描述

如果在运行 `setup-python-embedded.bat` 时出现类似以下错误：
- `'kdir' 不是内部或外部命令`
- `'cho' 不是内部或外部命令`
- 各种中文字符显示乱码并被当作命令执行

这通常是批处理文件的编码问题导致的。

## 解决方案

### 方法一：使用文本编辑器重新保存（推荐）

1. 使用 **Notepad++** 或 **VS Code** 打开 `setup-python-embedded.bat`
2. 在 Notepad++ 中：
   - 菜单：编码 → 转为 UTF-8 编码（无BOM）
   - 或者：编码 → 转为 ANSI 编码（GBK）
3. 保存文件
4. 重新运行脚本

### 方法二：使用 PowerShell 转换编码

在 PowerShell 中运行：

```powershell
# 转换为 UTF-8（无BOM）
$content = Get-Content setup-python-embedded.bat -Raw
[System.IO.File]::WriteAllText("setup-python-embedded.bat", $content, [System.Text.UTF8Encoding]::new($false))

# 或转换为 GBK（ANSI）
$content = Get-Content setup-python-embedded.bat -Raw -Encoding UTF8
$gbk = [System.Text.Encoding]::GetEncoding("GB2312")
[System.IO.File]::WriteAllText("setup-python-embedded.bat", $content, $gbk)
```

### 方法三：检查文件是否有隐藏字符

某些编辑器可能在文件中插入不可见字符。建议：
1. 使用专业的文本编辑器（如 VS Code、Notepad++）
2. 检查文件是否包含 BOM（字节顺序标记）
3. 确保文件以纯文本格式保存

## 推荐设置

- **编码格式**：UTF-8（无BOM）或 ANSI（GBK）
- **行尾格式**：CRLF（Windows）
- **编辑器**：VS Code、Notepad++、或 Sublime Text

## 注意事项

1. 批处理文件开头已设置 `chcp 65001`（UTF-8），但文件本身的编码仍需要正确
2. 某些中文标点符号（如全角括号、冒号）可能导致解析问题，已在脚本中修复
3. 如果问题持续，可以尝试使用 ANSI/GBK 编码保存文件

