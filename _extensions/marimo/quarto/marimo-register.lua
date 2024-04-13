local file_path = debug.getinfo(1, "S").source:sub(2)
local file_dir = file_path:match("(.*[/\\])")
local endpoint_path = file_dir .. "endpoint.py"
local missingMarimoCell = true

function CodeBlock(el)
  if el.attr and el.attr.classes:find_if(function (c) return string.match(c, "{?marimo}?") end) then
      converted_code = pandoc.pipe("python", {endpoint_path, "run"}, el.text)
      missingMarimoCell = false
      local block = pandoc.CodeBlock(converted_code)
      block.classes:insert("{marimo-key}")
      return block
  end
end

function Pandoc(doc)

  -- Do not attach webR as the page lacks any active webR cells
  if missingMarimoCell then
    return doc
  end

  -- Set the marimo app runnning after each cell
  -- is visited and we have collected all the content.
  pandoc.pipe("python", {endpoint_path, "execute"}, "")

  return doc
end
