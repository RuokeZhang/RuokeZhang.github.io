import java.util.concurrent.locks.*;
public class Test{
    public static int num=1;
    public static final Lock lock= new ReentrantLock();
    public static final Condition cond=lock.newCondition();
    public static void main(String[] args){
        new Thread(()->{
            lock.lock();
            try{
                while(num<=100){
                    System.out.println(num);
                    num+=1;
                    cond.signal();
                    if(num<=100){
                        cond.await();
                    }
                }
            }catch(Exception e){

            }finally{
                lock.unlock();
            }
        }).start();
        new Thread(()->{
            lock.lock();
            try{
                while(num<=100){
                    System.out.println(num);
                    num+=1;
                    cond.signal();
                    if(num<=100){
                        cond.await();
                    }
                }
            }catch(Exception e){

            }finally{
                lock.unlock();
            }
        }).start();
    }

}