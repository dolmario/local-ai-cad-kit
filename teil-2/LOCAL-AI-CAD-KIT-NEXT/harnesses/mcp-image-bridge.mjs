const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);

export function normalizeMcpImageResult(result) {
  const output = result?.output;
  if (!isObject(output) || !Array.isArray(output.content)) return result;
  const isImage = block => isObject(block) && block.type === 'image' &&
    typeof block.data === 'string' && typeof (block.mediaType ?? block.mimeType) === 'string' &&
    (block.mediaType ?? block.mimeType).startsWith('image/');
  if (!output.content.some(isImage)) return result;
  const content = output.content.map(block => {
    if (isImage(block)) {
      const {mimeType, ...rest} = block;
      return {...rest, mediaType: block.mediaType ?? mimeType};
    }
    if (isObject(block) && block.type === 'text' && typeof block.text === 'string') return block;
    return {type:'text', text:JSON.stringify(block)};
  });
  const {content: ignored, ...properties} = output;
  if (Object.keys(properties).length) content.push({type:'text', text:JSON.stringify(properties)});
  return {...result, output:content, isError:Boolean(result.isError || output.isError)};
}

export function createMcpImageHooks(previous = {}) {
  return {
    ...previous,
    async afterTool(context) {
      const prior = await previous.afterTool?.(context);
      if (prior?.stop) return prior;
      const result = prior?.result ?? context.result;
      const normalized = normalizeMcpImageResult(result);
      if (normalized === result) return prior;
      return {...prior, result:normalized};
    },
  };
}
