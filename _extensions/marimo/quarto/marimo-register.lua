local missingMarimoCell = true
local from_endpoint = require 'marimo-utils'.endpoint_fn(quarto.doc)
local default_meta = {}

-- Meta runs prior to CodeBlock, so we pass on info in Pandoc
function Meta(meta)
  if meta.execute == nil then
    return
  end
  for key, value in pairs(meta.execute) do
    default_meta[key] = value
  end
end

-- Hook functions to pandoc
function CodeBlock(el)
  if el.attr and el.attr.classes:find_if(function (c) return string.match(c, "{?marimo}?") end) then
      converted_code = from_endpoint("run", el.text)
      missingMarimoCell = false
      local block = pandoc.CodeBlock(converted_code)
      block.classes:insert("{marimo-key}")
      return block
  end
end

function Pandoc(doc)

  -- If no marimo cell is found, return the document as is.
  if missingMarimoCell then
    return doc
  end

  -- Set the marimo app runnning after each cell
  -- is visited and we have collected all the content.
  from_endpoint("execute", quarto.json.encode(default_meta))
  return doc
end
