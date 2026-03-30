from random import choice

async def rndemoji() -> str:
    '''Возвращает случайный эмодзи, олицетворяющий сеть, связь, содружество и т. п.'''
    emoji = choice(["🌐", "🕸️", "⛓️", "🤝"])
    return emoji