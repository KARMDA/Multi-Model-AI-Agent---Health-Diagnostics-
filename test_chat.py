from utils.llm_utils import get_llm

llm = get_llm()
print(llm.invoke("Hello"))
