from pydantic import BaseModel, Field
class CodeSubmission(BaseModel):
    code: str = Field(min_length=1)
    language: str = "cpp"
class JudgeResult(BaseModel):
    status: str
    accepted: bool
    runtime_ms: float | None = None
    memory_kb: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    compile_output: str | None = None
    message: str | None = None